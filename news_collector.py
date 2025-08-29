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
            # Bankruptcy terms
            "bankruptcy", "bankrupt", "chapter 11", "chapter 7", "insolvency",
            "filed for bankruptcy", "liquidation", "financial collapse",
            
            # Closure terms  
            "closure", "shutdown", "closing down", "going out of business",
            "ceased operations", "wind down", "store closures", "closing stores",
            "plant closure", "facility shutdown", "business closure",
            
            # Job loss terms
            "layoffs", "mass layoffs", "cutting jobs", "firing", "downsizing",
            "job cuts", "workforce reduction", "eliminating jobs", "staff reduction",
            "redundancies", "pink slips", "employment cuts", "terminations",
            
            # Financial distress
            "losses", "failing", "collapse", "decline", "crisis", "struggling",
            "financial troubles", "cash flow problems", "debt crisis", "revenue decline",
            "profit decline", "financial distress", "funding crisis", "cost cutting",
            
            # Corporate restructuring
            "restructuring", "reorganization", "asset sales", "divestiture",
            "spin off", "breakup", "downsizing", "rightsizing", "cost reduction",
            
            # Market performance
            "shares fall", "stock drops", "market decline", "investor concerns",
            "disappointing results", "missed earnings", "guidance cut", "outlook lowered",
            "warning issued", "profit warning", "revenue warning",
            
            # Business challenges
            "supply chain issues", "production halt", "recall", "investigation",
            "regulatory issues", "compliance problems", "lawsuit", "legal troubles",
            "scandal", "fraud", "misconduct", "penalty", "fine"
        ]
        
        # Expanded RSS feeds for comprehensive business news coverage
        self.rss_feeds = [
            # Major News Networks
            "https://feeds.reuters.com/reuters/businessNews",
            "https://rss.cnn.com/rss/money_news_companies.rss", 
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://www.cnbc.com/id/10000664/device/rss/rss.html",
            "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
            "https://feeds.fortune.com/fortune/headlines",
            "https://www.wsj.com/xml/rss/3_7455.xml",
            
            # Financial News
            "https://feeds.finance.yahoo.com/rss/2.0/headline",
            "https://www.ft.com/rss/companies",
            "https://www.businessinsider.com/rss",
            "https://feeds.feedburner.com/typepad/alleyinsider/silicon_alley_insider",
            "https://www.economist.com/business/rss.xml",
            "https://feeds.feedburner.com/barrons/topstories",
            "https://feeds.feedburner.com/investorplace/stocks",
            
            # Tech & Startup News  
            "https://techcrunch.com/feed/",
            "https://feeds.feedburner.com/venturebeat/SZYF",
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://www.theverge.com/rss/index.xml",
            "https://feeds.feedburner.com/crunchbase_news",
            
            # Industry-Specific
            "https://feeds.retail-week.com/retail-week/news",
            "https://www.retaildive.com/feeds/news/",
            "https://feeds.constructiondive.com/constructiondive",
            "https://www.manufacturingdive.com/feeds/news/",
            "https://www.restaurantdive.com/feeds/news/",
            "https://www.utilitydive.com/feeds/news/",
            "https://www.bankingdive.com/feeds/news/",
            "https://www.biopharmadive.com/feeds/news/",
            
            # Regional Business News
            "https://feeds.seattletimes.com/businesstechnology/",
            "https://www.latimes.com/business/rss2.0.xml",
            "https://feeds.chicagotribune.com/chicagotribune/business",
            "https://feeds.boston.com/boston/business",
            "https://feeds.washingtonpost.com/rss/business",
            
            # International Business
            "https://feeds.bbci.co.uk/news/business/rss.xml",
            "https://feeds.feedburner.com/ndtvprofit-latest",
            "https://feeds.reuters.com/reuters/UKBusinessNews",
            "https://www.scmp.com/rss/91/feed",
            "https://feeds.reuters.com/reuters/JPBusinessNews",
            
            # Alternative & Independent
            "https://feeds.feedburner.com/zerohedge/feed",
            "https://feeds.feedburner.com/entrepreneur/latest",
            "https://feeds.inc.com/home/updates",
            "https://feeds.hbr.org/harvardbusiness",
            "https://feeds.feedburner.com/fastcompany/headlines",
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
                        if sentiment <= 0.4 or len(found_keywords) >= 2:  # Include if multiple negative keywords
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
                                
                                if sentiment <= 0.4 or len(found_keywords) >= 2:
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
        """Save articles to database with auto-cleanup"""
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
        
        # Auto-cleanup after every 5 new articles
        if saved_count >= 5:
            cursor.execute('''
            DELETE FROM negative_news 
            WHERE created_at < datetime('now', '-48 hours')
            ''')
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"🧹 Auto-cleanup: Deleted {deleted_count} articles older than 48 hours")
        
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
    
    def fetch_linkedin_trending(self) -> List[Dict]:
        """Fetch trending business news from LinkedIn via search scraping"""
        articles = []
        
        try:
            # LinkedIn trending business keywords to search for
            trending_queries = [
                "layoffs", "bankruptcy", "company closure", "business failure",
                "restructuring", "downsizing", "financial crisis", "merger failed"
            ]
            
            for query in trending_queries:
                try:
                    # Use DuckDuckGo to search for LinkedIn posts about business crises
                    search_url = f"https://duckduckgo.com/html/?q=site:linkedin.com {query} business news"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    response = requests.get(search_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        # Simple extraction of LinkedIn URLs
                        import re
                        linkedin_urls = re.findall(r'href="([^"]*linkedin\.com[^"]*)"', response.text)
                        
                        for url in linkedin_urls[:3]:  # Limit to prevent spam
                            if 'posts' in url or 'pulse' in url:
                                # Create article entry for LinkedIn trending
                                articles.append({
                                    'title': f"LinkedIn Trending: {query.title()} Discussion",
                                    'link': url,
                                    'description': f"Trending discussion about {query} in business community",
                                    'published': datetime.datetime.now().isoformat(),
                                    'source': 'LinkedIn Trending',
                                    'sentiment_score': -0.3,  # Assume negative for crisis topics
                                    'negative_keywords': query
                                })
                    
                    time.sleep(2)  # Rate limiting
                except Exception as e:
                    print(f"Error fetching LinkedIn trending for '{query}': {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in LinkedIn trending fetch: {e}")
        
        return articles[:10]  # Return top 10
    
    def fetch_additional_sources(self) -> List[Dict]:
        """Fetch from additional sources to ensure we have enough articles"""
        articles = []
        
        # Additional news APIs and sources
        additional_sources = [
            "https://feeds.feedburner.com/businessweek/blog/bloomberg",
            "https://feeds.feedburner.com/time/business",
            "https://feeds.feedburner.com/usnews/business",
            "https://feeds.npr.org/1006/rss.xml",  # NPR Business
            "https://feeds.abcnews.com/abcnews/businessheadlines",
            "https://feeds.foxbusiness.com/foxbusiness/latest",
            "https://feeds.reuters.com/reuters/UKBankingNews",
            "https://www.investing.com/rss/news.rss",
            "https://feeds.ign.com/ign/all",  # Sometimes covers business gaming news
            "https://feeds.feedburner.com/venturebeat/games-beat"
        ]
        
        for feed_url in additional_sources:
            try:
                print(f"Fetching additional from: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Limit per feed
                    title = entry.get('title', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    full_text = f"{title} {description}"
                    
                    found_keywords = self.contains_negative_keywords(full_text)
                    
                    if found_keywords:
                        sentiment = self.analyze_sentiment(full_text)
                        
                        if sentiment <= 0.4 or len(found_keywords) >= 2:  # More lenient to get more articles
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
                            articles.append(article)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error fetching additional from {feed_url}: {e}")
                continue
        
        return articles

    def update_news(self, newsapi_key=None, min_articles=100):
        """Main method to update news database - ensures minimum article count"""
        print("Starting comprehensive news collection...")
        
        # Fetch from main RSS feeds
        rss_articles = self.fetch_news_from_rss()
        print(f"Found {len(rss_articles)} negative articles from main RSS feeds")
        
        # Fetch from NewsAPI if key provided
        newsapi_articles = []
        if newsapi_key:
            newsapi_articles = self.fetch_news_from_newsapi(newsapi_key)
            print(f"Found {len(newsapi_articles)} negative articles from NewsAPI")
        
        # Fetch LinkedIn trending
        linkedin_articles = self.fetch_linkedin_trending()
        print(f"Found {len(linkedin_articles)} trending articles from LinkedIn")
        
        # Combine all articles
        all_articles = rss_articles + newsapi_articles + linkedin_articles
        
        # If we don't have enough articles, fetch from additional sources
        if len(all_articles) < min_articles:
            print(f"Need more articles ({len(all_articles)}/{min_articles}), fetching additional sources...")
            additional_articles = self.fetch_additional_sources()
            all_articles.extend(additional_articles)
            print(f"Added {len(additional_articles)} articles from additional sources")
        
        # Continue fetching until we have enough (or exhaust sources)
        attempts = 0
        while len(all_articles) < min_articles and attempts < 3:
            print(f"Still need more articles ({len(all_articles)}/{min_articles}), trying broader search...")
            broader_articles = self.fetch_additional_sources()
            all_articles.extend(broader_articles)
            attempts += 1
        
        # Remove duplicates based on URL
        unique_articles = []
        seen_urls = set()
        for article in all_articles:
            if article['link'] not in seen_urls and article['link']:
                unique_articles.append(article)
                seen_urls.add(article['link'])
        
        print(f"Total unique articles collected: {len(unique_articles)}")
        
        # Save to database
        saved_count = self.save_articles(unique_articles)
        print(f"Saved {saved_count} new articles to database")
        
        return saved_count

if __name__ == "__main__":
    # Try enhanced collector first, fallback to standard
    try:
        from enhanced_collector import EnhancedNegativeNewsCollector
        print("🚀 Using Enhanced Collector with 100+ sources...")
        collector = EnhancedNegativeNewsCollector()
        saved, total = collector.comprehensive_update(min_articles=100)
        print(f"Enhanced collection complete: {saved} saved, {total} total")
    except Exception as e:
        print(f"Enhanced collector failed ({e}), using standard collector...")
        collector = NegativeNewsCollector()
        newsapi_key = os.getenv('NEWSAPI_KEY')
        collector.update_news(newsapi_key)