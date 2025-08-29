import feedparser
import requests
import sqlite3
import datetime
from textblob import TextBlob
import json
import time
import os
from typing import List, Dict
import re

class NegativeNewsCollector:
    def __init__(self, db_path="news_data.db"):
        self.db_path = db_path
        self.negative_keywords = [
            "bankruptcy", "bankrupt", "closure", "shutdown", "layoffs", 
            "losses", "failing", "collapse", "decline", "crisis",
            "struggling", "cutting jobs", "firing", "downsizing",
            "closing down", "going out of business", "liquidation",
            "restructuring", "chapter 11", "chapter 7", "insolvency",
            "filed for bankruptcy", "ceased operations", "wind down",
            "mass layoffs", "store closures", "closing stores", "financial troubles"
        ]
        
        # RSS feeds for business news
        self.rss_feeds = [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://rss.cnn.com/rss/money_news_companies.rss",
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://www.cnbc.com/id/10000664/device/rss/rss.html",
            "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
            "https://feeds.fortune.com/fortune/headlines",
            "https://www.wsj.com/xml/rss/3_7455.xml"
        ]
        
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS negative_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            description TEXT,
            published DATE,
            source TEXT,
            sentiment_score REAL,
            negative_keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment using TextBlob"""
        try:
            clean_text = self.clean_html(text)
            blob = TextBlob(clean_text)
            return blob.sentiment.polarity
        except:
            return 0.0
    
    def contains_negative_keywords(self, text: str) -> List[str]:
        """Check if text contains negative business keywords"""
        text_lower = self.clean_html(text).lower()
        found_keywords = []
        
        for keyword in self.negative_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def fetch_news_from_rss(self) -> List[Dict]:
        """Fetch news from RSS feeds"""
        all_articles = []
        
        for feed_url in self.rss_feeds:
            try:
                print(f"Fetching from: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Combine title and description for analysis
                    title = entry.get('title', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    full_text = f"{title} {description}"
                    
                    # Check for negative keywords
                    found_keywords = self.contains_negative_keywords(full_text)
                    
                    if found_keywords:
                        # Calculate sentiment
                        sentiment = self.analyze_sentiment(full_text)
                        
                        # Only include if sentiment is negative or neutral with strong negative keywords
                        if sentiment <= 0.2:  # More lenient threshold
                            # Parse published date
                            published = entry.get('published', '')
                            if not published:
                                published = entry.get('updated', '')
                            
                            article = {
                                'title': title,
                                'link': entry.get('link', ''),
                                'description': self.clean_html(description),
                                'published': published,
                                'source': feed.feed.get('title', feed_url.split('//')[1].split('/')[0]),
                                'sentiment_score': sentiment,
                                'negative_keywords': ','.join(found_keywords)
                            }
                            all_articles.append(article)
                
                time.sleep(1)  # Be polite to servers
                
            except Exception as e:
                print(f"Error fetching from {feed_url}: {e}")
                continue
        
        return all_articles
    
    def fetch_news_from_newsapi(self, api_key: str) -> List[Dict]:
        """Fetch news from NewsAPI"""
        if not api_key:
            return []
        
        articles = []
        
        # Search for negative business news
        negative_queries = [
            "business bankruptcy OR company closure OR layoffs",
            "business shutdown OR company liquidation",
            "business losses OR financial troubles OR restructuring"
        ]
        
        for query in negative_queries:
            try:
                url = f"https://newsapi.org/v2/everything"
                params = {
                    'q': query,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 50,
                    'apiKey': api_key,
                    'domains': 'bloomberg.com,reuters.com,cnbc.com,marketwatch.com,wsj.com,fortune.com'
                }
                
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'ok':
                        for article in data.get('articles', []):
                            title = article.get('title', '')
                            description = article.get('description', '')
                            full_text = f"{title} {description}"
                            found_keywords = self.contains_negative_keywords(full_text)
                            
                            if found_keywords:
                                sentiment = self.analyze_sentiment(full_text)
                                
                                if sentiment <= 0.2:
                                    articles.append({
                                        'title': title,
                                        'link': article.get('url', ''),
                                        'description': description,
                                        'published': article.get('publishedAt', ''),
                                        'source': article.get('source', {}).get('name', 'NewsAPI'),
                                        'sentiment_score': sentiment,
                                        'negative_keywords': ','.join(found_keywords)
                                    })
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error with NewsAPI query '{query}': {e}")
                continue
        
        return articles
    
    def save_articles(self, articles: List[Dict]):
        """Save articles to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        
        for article in articles:
            try:
                cursor.execute('''
                INSERT OR IGNORE INTO negative_news 
                (title, link, description, published, source, sentiment_score, negative_keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article['title'],
                    article['link'],
                    article['description'],
                    article['published'],
                    article['source'],
                    article['sentiment_score'],
                    article['negative_keywords']
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
                    
            except Exception as e:
                print(f"Error saving article: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return saved_count
    
    def get_recent_news(self, days=7) -> List[Dict]:
        """Get recent negative news from database, sorted by newest first"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT title, link, description, published, source, sentiment_score, negative_keywords, created_at
        FROM negative_news 
        WHERE created_at >= datetime('now', '-{} days')
        ORDER BY created_at DESC, published DESC
        '''.format(days))
        
        rows = cursor.fetchall()
        conn.close()
        
        articles = []
        for row in rows:
            articles.append({
                'title': row[0],
                'link': row[1],
                'description': row[2],
                'published': row[3],
                'source': row[4],
                'sentiment_score': row[5],
                'negative_keywords': row[6],
                'created_at': row[7]
            })
        
        return articles
    
    def update_news(self, newsapi_key=None):
        """Main method to update news database"""
        print("Starting news collection...")
        
        # Fetch from RSS feeds
        rss_articles = self.fetch_news_from_rss()
        print(f"Found {len(rss_articles)} negative articles from RSS feeds")
        
        # Fetch from NewsAPI if key provided
        newsapi_articles = []
        if newsapi_key:
            newsapi_articles = self.fetch_news_from_newsapi(newsapi_key)
            print(f"Found {len(newsapi_articles)} negative articles from NewsAPI")
        
        # Combine all articles
        all_articles = rss_articles + newsapi_articles
        
        # Remove duplicates based on URL
        unique_articles = []
        seen_urls = set()
        for article in all_articles:
            if article['link'] not in seen_urls and article['link']:
                unique_articles.append(article)
                seen_urls.add(article['link'])
        
        # Save to database
        saved_count = self.save_articles(unique_articles)
        print(f"Saved {saved_count} new articles to database")
        
        return saved_count

if __name__ == "__main__":
    collector = NegativeNewsCollector()
    
    # Try to get NewsAPI key from environment
    newsapi_key = os.getenv('NEWSAPI_KEY')
    
    # Update news
    collector.update_news(newsapi_key)