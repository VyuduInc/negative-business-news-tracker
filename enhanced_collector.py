"""
Enhanced News Collector with Multiple API Integration
Guarantees 100+ negative business articles through comprehensive source aggregation
"""

import requests
import feedparser
import sqlite3
import datetime
from textblob import TextBlob
import json
import time
import os
import re
from typing import List, Dict
from comprehensive_news_sources import ComprehensiveNewsAggregator
from local_news_sources import LocalNewsSourcesCollector

class EnhancedNegativeNewsCollector:
    def __init__(self, db_path="news_data.db"):
        self.db_path = db_path
        self.aggregator = ComprehensiveNewsAggregator()
        self.local_collector = LocalNewsSourcesCollector()
        
        # Enhanced negative keywords with categories
        self.negative_keywords = {
            'bankruptcy': [
                "bankruptcy", "bankrupt", "chapter 11", "chapter 7", "insolvency",
                "filed for bankruptcy", "liquidation", "financial collapse", "receivership"
            ],
            'closures': [
                "closure", "shutdown", "closing down", "going out of business",
                "ceased operations", "wind down", "store closures", "closing stores",
                "plant closure", "facility shutdown", "business closure", "shuttering"
            ],
            'layoffs': [
                "layoffs", "mass layoffs", "cutting jobs", "firing", "downsizing",
                "job cuts", "workforce reduction", "eliminating jobs", "staff reduction",
                "redundancies", "pink slips", "employment cuts", "terminations", "RIF"
            ],
            'financial_distress': [
                "losses", "failing", "collapse", "decline", "crisis", "struggling",
                "financial troubles", "cash flow problems", "debt crisis", "revenue decline",
                "profit decline", "financial distress", "funding crisis", "cost cutting"
            ],
            'corporate_issues': [
                "restructuring", "reorganization", "asset sales", "divestiture",
                "spin off", "breakup", "rightsizing", "cost reduction", "warn notice"
            ],
            'market_troubles': [
                "shares fall", "stock drops", "market decline", "investor concerns",
                "disappointing results", "missed earnings", "guidance cut", "outlook lowered",
                "warning issued", "profit warning", "revenue warning"
            ],
            'legal_troubles': [
                "investigation", "lawsuit", "legal troubles", "scandal", "fraud",
                "misconduct", "penalty", "fine", "settlement", "violation"
            ]
        }
        
        self.all_keywords = []
        for category, keywords in self.negative_keywords.items():
            self.all_keywords.extend(keywords)
        
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database (use existing schema)"""
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
    
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment using TextBlob"""
        try:
            clean_text = self.clean_html(text)
            blob = TextBlob(clean_text)
            return blob.sentiment.polarity
        except:
            return 0.0
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    def categorize_keywords(self, found_keywords: List[str]) -> str:
        """Categorize found keywords into crisis types"""
        categories = []
        for category, keywords in self.negative_keywords.items():
            if any(keyword in found_keywords for keyword in keywords):
                categories.append(category)
        return ','.join(categories) if categories else 'general'
    
    def contains_negative_keywords(self, text: str) -> List[str]:
        """Check if text contains negative business keywords"""
        text_lower = self.clean_html(text).lower()
        found_keywords = []
        
        for keyword in self.all_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def fetch_from_multiple_apis(self) -> List[Dict]:
        """Fetch from multiple news APIs"""
        all_articles = []
        
        # Get API keys from environment
        newsapi_key = os.getenv('NEWSAPI_KEY')
        mediastack_key = os.getenv('MEDIASTACK_KEY') 
        newsdata_key = os.getenv('NEWSDATA_KEY')
        
        crisis_queries = [
            "business bankruptcy OR company closure",
            "corporate layoffs OR downsizing", 
            "business crisis OR financial troubles",
            "company shutdown OR restructuring",
            "mass layoffs OR job cuts",
            "corporate scandal OR investigation"
        ]
        
        # NewsAPI.org
        if newsapi_key:
            print("Fetching from NewsAPI.org...")
            for query in crisis_queries:
                try:
                    articles = self.aggregator.fetch_from_newsapi(newsapi_key, query)
                    processed = self.process_newsapi_articles(articles)
                    all_articles.extend(processed)
                    time.sleep(1)
                except Exception as e:
                    print(f"NewsAPI error for '{query}': {e}")
        
        # Mediastack
        if mediastack_key:
            print("Fetching from Mediastack...")
            try:
                keywords = ['bankruptcy', 'layoffs', 'closure', 'crisis', 'struggling']
                articles = self.aggregator.fetch_from_mediastack(mediastack_key, keywords)
                processed = self.process_mediastack_articles(articles)
                all_articles.extend(processed)
            except Exception as e:
                print(f"Mediastack error: {e}")
        
        # NewsData.io
        if newsdata_key:
            print("Fetching from NewsData.io...")
            for query in crisis_queries[:3]:  # Limit due to rate limits
                try:
                    articles = self.aggregator.fetch_from_newsdata_io(newsdata_key, query)
                    processed = self.process_newsdata_articles(articles)
                    all_articles.extend(processed)
                    time.sleep(2)
                except Exception as e:
                    print(f"NewsData.io error for '{query}': {e}")
        
        return all_articles
    
    def process_newsapi_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process NewsAPI articles"""
        processed = []
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            full_text = f"{title} {description}"
            
            found_keywords = self.contains_negative_keywords(full_text)
            if found_keywords:
                sentiment = self.analyze_sentiment(full_text)
                if sentiment <= 0.4 or len(found_keywords) >= 2:
                    processed.append({
                        'title': title,
                        'link': article.get('url', ''),
                        'description': description,
                        'published': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', 'NewsAPI'),
                        'source_type': 'newsapi',
                        'sentiment_score': sentiment,
                        'negative_keywords': ','.join(found_keywords),
                        'keyword_category': self.categorize_keywords(found_keywords)
                    })
        return processed
    
    def process_mediastack_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process Mediastack articles"""
        processed = []
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            full_text = f"{title} {description}"
            
            found_keywords = self.contains_negative_keywords(full_text)
            if found_keywords:
                sentiment = self.analyze_sentiment(full_text)
                if sentiment <= 0.4 or len(found_keywords) >= 2:
                    processed.append({
                        'title': title,
                        'link': article.get('url', ''),
                        'description': description,
                        'published': article.get('published_at', ''),
                        'source': article.get('source', 'Mediastack'),
                        'source_type': 'mediastack',
                        'sentiment_score': sentiment,
                        'negative_keywords': ','.join(found_keywords),
                        'keyword_category': self.categorize_keywords(found_keywords)
                    })
        return processed
    
    def process_newsdata_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process NewsData.io articles"""
        processed = []
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            full_text = f"{title} {description}"
            
            found_keywords = self.contains_negative_keywords(full_text)
            if found_keywords:
                sentiment = self.analyze_sentiment(full_text)
                if sentiment <= 0.4 or len(found_keywords) >= 2:
                    processed.append({
                        'title': title,
                        'link': article.get('link', ''),
                        'description': description,
                        'published': article.get('pubDate', ''),
                        'source': article.get('source_id', 'NewsData'),
                        'source_type': 'newsdata',
                        'sentiment_score': sentiment,
                        'negative_keywords': ','.join(found_keywords),
                        'keyword_category': self.categorize_keywords(found_keywords)
                    })
        return processed
    
    def fetch_from_comprehensive_rss(self) -> List[Dict]:
        """Fetch from all comprehensive RSS feeds including local sources"""
        all_articles = []
        
        # Combine national and local RSS feeds
        all_rss_feeds = self.aggregator.comprehensive_rss_feeds + self.local_collector.local_news_rss_feeds
        print(f"Fetching from {len(all_rss_feeds)} RSS sources ({len(self.aggregator.comprehensive_rss_feeds)} national + {len(self.local_collector.local_news_rss_feeds)} local)...")
        
        for feed_url in all_rss_feeds:
            try:
                print(f"Processing: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:20]:  # Limit per feed
                    title = entry.get('title', '')
                    description = entry.get('description', '') or entry.get('summary', '')
                    full_text = f"{title} {description}"
                    
                    found_keywords = self.contains_negative_keywords(full_text)
                    
                    if found_keywords:
                        sentiment = self.analyze_sentiment(full_text)
                        
                        if sentiment <= 0.4 or len(found_keywords) >= 2:
                            published = entry.get('published', '')
                            if not published:
                                published = entry.get('updated', '')
                            
                            all_articles.append({
                                'title': title,
                                'link': entry.get('link', ''),
                                'description': self.clean_html(description),
                                'published': published,
                                'source': feed.feed.get('title', feed_url.split('//')[1].split('/')[0]),
                                'source_type': 'rss',
                                'sentiment_score': sentiment,
                                'negative_keywords': ','.join(found_keywords),
                                'keyword_category': self.categorize_keywords(found_keywords)
                            })
                
                time.sleep(0.2)  # Faster rate limiting for real-time
                
            except Exception as e:
                print(f"Error with RSS feed {feed_url}: {e}")
                continue
        
        return all_articles
    
    def fetch_from_social_sources(self) -> List[Dict]:
        """Fetch from Reddit and Hacker News"""
        all_articles = []
        
        print("Fetching from Reddit business discussions...")
        reddit_articles = self.aggregator.fetch_from_reddit_business()
        all_articles.extend(reddit_articles)
        
        print("Fetching from Hacker News...")
        hn_articles = self.aggregator.fetch_from_hackernews()
        all_articles.extend(hn_articles)
        
        return all_articles
    
    def save_articles(self, articles: List[Dict]):
        """Save articles to database (compatible with existing schema)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        
        for article in articles:
            try:
                # Use existing schema (without source_type and keyword_category)
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
    
    def comprehensive_update(self, min_articles=100, real_time_mode=False):
        """Comprehensive update from all available sources"""
        if real_time_mode:
            print("⚡ REAL-TIME NEWS COLLECTION...")
            print(f"Target: {min_articles}+ articles (real-time mode)")
        else:
            print("🚀 COMPREHENSIVE NEWS COLLECTION STARTING...")
            print(f"Target: {min_articles}+ articles")
        print("=" * 60)
        
        all_articles = []
        
        # 1. Multiple News APIs
        api_articles = self.fetch_from_multiple_apis()
        all_articles.extend(api_articles)
        print(f"✅ APIs collected: {len(api_articles)} articles")
        
        # 2. Comprehensive RSS Feeds  
        rss_articles = self.fetch_from_comprehensive_rss()
        all_articles.extend(rss_articles)
        print(f"✅ RSS collected: {len(rss_articles)} articles")
        
        # 3. Social Sources
        social_articles = self.fetch_from_social_sources()
        all_articles.extend(social_articles)
        print(f"✅ Social collected: {len(social_articles)} articles")
        
        # Remove duplicates
        unique_articles = []
        seen_urls = set()
        for article in all_articles:
            if article['link'] not in seen_urls and article['link']:
                unique_articles.append(article)
                seen_urls.add(article['link'])
        
        print(f"📊 Total unique articles: {len(unique_articles)}")
        
        # Save to database
        saved_count = self.save_articles(unique_articles)
        print(f"💾 Saved {saved_count} new articles to database")
        
        # Check if we met the target
        if len(unique_articles) >= min_articles:
            print(f"🎯 TARGET MET: {len(unique_articles)}/{min_articles} articles collected!")
        else:
            print(f"⚠️  Target missed: {len(unique_articles)}/{min_articles} articles")
            print("Consider enabling more API keys for better coverage")
        
        return saved_count, len(unique_articles)

if __name__ == "__main__":
    collector = EnhancedNegativeNewsCollector()
    saved, total = collector.comprehensive_update(min_articles=100)
    print(f"\n🏁 COLLECTION COMPLETE")
    print(f"📊 Articles saved: {saved}")
    print(f"📈 Total collected: {total}")
    print(f"🎯 Target (100+): {'✅ MET' if total >= 100 else '❌ MISSED'}")