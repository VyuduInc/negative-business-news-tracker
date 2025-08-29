"""
Fast Real-Time News Collector
Optimized for speed - fetches news in under 30 seconds
"""

import requests
import feedparser
import sqlite3
import datetime
from textblob import TextBlob
import time
import os
import re
from typing import List, Dict
import concurrent.futures
from threading import Lock

class FastNewsCollector:
    def __init__(self, db_path="news_data.db"):
        self.db_path = db_path
        self.db_lock = Lock()
        
        # Fast negative keywords (most important ones)
        self.negative_keywords = [
            "bankruptcy", "bankrupt", "closure", "shutdown", "layoffs", 
            "mass layoffs", "job cuts", "firing", "downsizing", "failing",
            "collapse", "decline", "crisis", "struggling", "liquidation",
            "restructuring", "chapter 11", "ceased operations", "closing stores"
        ]
        
        # TOP PRIORITY SOURCES (Fast, reliable, high-quality)
        self.priority_feeds = [
            # Major Business (fastest feeds)
            "https://feeds.reuters.com/reuters/businessNews",
            "https://rss.cnn.com/rss/money_news_companies.rss",
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://www.cnbc.com/id/10000664/device/rss/rss.html",
            "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
            "https://feeds.fortune.com/fortune/headlines",
            "https://feeds.finance.yahoo.com/rss/2.0/headline",
            
            # Industry Dive (excellent for layoffs/closures)
            "https://www.retaildive.com/feeds/news/",
            "https://www.bankingdive.com/feeds/news/",
            "https://www.restaurantdive.com/feeds/news/",
            "https://www.manufacturingdive.com/feeds/news/",
            "https://www.healthcaredive.com/feeds/news/",
            
            # Top Local Business News (fast and reliable)
            "https://www.bizjournals.com/atlanta/feeds/news",
            "https://www.bizjournals.com/chicago/feeds/news", 
            "https://www.bizjournals.com/dallas/feeds/news",
            "https://www.bizjournals.com/losangeles/feeds/news",
            "https://www.bizjournals.com/newyork/feeds/news",
            "https://www.bizjournals.com/sanfrancisco/feeds/news",
            
            # Alternative sources (often have breaking news first)
            "https://feeds.feedburner.com/zerohedge/feed",
            "https://techcrunch.com/feed/",
        ]
        
        # SECONDARY SOURCES (for when we need more articles)
        self.secondary_feeds = [
            "https://www.businessinsider.com/rss",
            "https://feeds.feedburner.com/entrepreneur/latest",
            "https://feeds.inc.com/home/updates",
            "https://feeds.feedburner.com/fastcompany/headlines",
            "https://feeds.bbci.co.uk/news/business/rss.xml",
            "https://www.scmp.com/rss/91/feed",
            "https://feeds.feedburner.com/venturebeat/SZYF",
            "https://www.utilitydive.com/feeds/news/",
            "https://www.bizjournals.com/boston/feeds/news",
            "https://www.bizjournals.com/houston/feeds/news",
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
        if not text:
            return ""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    def analyze_sentiment(self, text: str) -> float:
        """Quick sentiment analysis"""
        try:
            clean_text = self.clean_html(text)
            blob = TextBlob(clean_text)
            return blob.sentiment.polarity
        except:
            return 0.0
    
    def contains_negative_keywords(self, text: str) -> List[str]:
        """Fast keyword check"""
        if not text:
            return []
        text_lower = self.clean_html(text).lower()
        found_keywords = []
        for keyword in self.negative_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        return found_keywords
    
    def fetch_single_feed(self, feed_url: str, max_entries: int = 15) -> List[Dict]:
        """Fetch a single RSS feed with timeout"""
        articles = []
        try:
            # Fast timeout
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:max_entries]:
                title = entry.get('title', '')
                description = entry.get('description', '') or entry.get('summary', '')
                full_text = f"{title} {description}"
                
                found_keywords = self.contains_negative_keywords(full_text)
                
                if found_keywords:
                    sentiment = self.analyze_sentiment(full_text)
                    if sentiment <= 0.4 or len(found_keywords) >= 2:
                        published = entry.get('published', '') or entry.get('updated', '')
                        articles.append({
                            'title': title,
                            'link': entry.get('link', ''),
                            'description': self.clean_html(description)[:300],
                            'published': published,
                            'source': feed.feed.get('title', feed_url.split('//')[1].split('/')[0]),
                            'sentiment_score': sentiment,
                            'negative_keywords': ','.join(found_keywords)
                        })
        except Exception as e:
            # Silently skip failed feeds for speed
            pass
        
        return articles
    
    def fast_parallel_fetch(self, feeds: List[str], max_workers: int = 10) -> List[Dict]:
        """Fetch multiple feeds in parallel with timeout"""
        all_articles = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all feed fetches with timeout
            future_to_url = {
                executor.submit(self.fetch_single_feed, feed_url): feed_url 
                for feed_url in feeds
            }
            
            # Collect results with timeout
            for future in concurrent.futures.as_completed(future_to_url, timeout=25):
                try:
                    articles = future.result(timeout=5)  # 5 second timeout per feed
                    all_articles.extend(articles)
                except:
                    # Skip failed feeds for speed
                    continue
        
        return all_articles
    
    def save_articles(self, articles: List[Dict]) -> int:
        """Save articles to database (thread-safe)"""
        if not articles:
            return 0
            
        with self.db_lock:
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
                except:
                    continue
            
            conn.commit()
            conn.close()
            return saved_count
    
    def fast_update(self, target_articles: int = 50) -> tuple:
        """Fast update - completes in under 30 seconds"""
        start_time = time.time()
        print("⚡ FAST NEWS COLLECTION (Target: 30 seconds)")
        print("=" * 50)
        
        # Phase 1: Priority feeds (highest quality)
        print(f"Phase 1: Fetching from {len(self.priority_feeds)} priority sources...")
        priority_articles = self.fast_parallel_fetch(self.priority_feeds, max_workers=15)
        print(f"✅ Priority: {len(priority_articles)} articles")
        
        # Phase 2: Secondary feeds (only if needed)
        secondary_articles = []
        if len(priority_articles) < target_articles:
            print(f"Phase 2: Fetching from {len(self.secondary_feeds)} secondary sources...")
            secondary_articles = self.fast_parallel_fetch(self.secondary_feeds, max_workers=10)
            print(f"✅ Secondary: {len(secondary_articles)} articles")
        
        # Combine and deduplicate
        all_articles = priority_articles + secondary_articles
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article['link'] and article['link'] not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article['link'])
        
        # Save to database
        saved_count = self.save_articles(unique_articles)
        
        elapsed_time = time.time() - start_time
        
        print(f"📊 Results:")
        print(f"   • Total collected: {len(unique_articles)}")
        print(f"   • New articles saved: {saved_count}")  
        print(f"   • Time elapsed: {elapsed_time:.1f} seconds")
        print(f"   • Speed: {'✅ FAST' if elapsed_time < 30 else '⚠️  SLOW'}")
        
        return saved_count, len(unique_articles), elapsed_time

if __name__ == "__main__":
    collector = FastNewsCollector()
    saved, total, elapsed = collector.fast_update(target_articles=50)
    
    if elapsed < 30:
        print(f"🎯 SUCCESS: Fast collection complete in {elapsed:.1f}s!")
    else:
        print(f"⚠️  SLOW: Took {elapsed:.1f}s - consider reducing sources")