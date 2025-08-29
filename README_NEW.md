# 📉 Negative Business News Tracker

A comprehensive web application that tracks and displays negative business news including bankruptcies, closures, layoffs, and financial difficulties from major news sources.

## ✅ FULLY FUNCTIONAL - READY TO USE!

**Current Status**: ✅ Complete and working  
**Local Dashboard**: http://localhost:8501  
**Articles Tracked**: 4 negative business articles already collected  
**All Links**: ✅ Clickable and working  
**Sorting**: ✅ Newest to oldest confirmed  

## ✨ Features

- **Multi-Source Data Collection**: Aggregates news from 7+ major sources (Reuters, Bloomberg, CNN, CNBC, MarketWatch, Fortune, WSJ)
- **Intelligent Filtering**: Uses sentiment analysis and keyword matching to identify negative business news
- **Real-Time Updates**: Automated data refresh every 12-24 hours when deployed
- **Interactive Dashboard**: Streamlit-powered UI with charts, filters, and analytics
- **Clickable Links**: All articles link directly to the source for full reading
- **Sorted Display**: Articles displayed newest first for latest updates
- **Cloud Deployment**: Ready for Modal cloud deployment with scheduled updates

## 🚀 Quick Start

### Already Running Locally!
The app is currently running at: **http://localhost:8501**

### Manual Setup (if needed)
```bash
# Environment already created, but if you need to recreate:
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Collect initial data (already done)
python news_collector.py

# Launch dashboard (already running)
streamlit run app.py
```

## 📊 Currently Tracked Articles

1. **Lynas Rare Earths Shares Fall After A$750 Million Equity Raise** (Bloomberg)
2. **Dell Falls After Reporting Tighter Profit Margins on Servers** (Bloomberg)  
3. **Trump's Cook firing will likely end up in the Supreme Court's hands** (CNBC)
4. **When 'invest like the 1%' fails: How Yieldstreet's real estate bets left customers with massive losses** (CNBC)

All articles are properly sorted (newest first) with working clickable links to the full stories.

## 🔄 Auto-Updates

- **Manual**: Click "Refresh News Data" in sidebar
- **Scheduled**: Every 12 hours when deployed to Modal
- **Sources**: 7 RSS feeds + optional NewsAPI

## 🎯 Verified Features

✅ **Data Collection**: RSS feeds from 7 major news sources  
✅ **Sentiment Analysis**: TextBlob-powered negative sentiment detection  
✅ **Keyword Filtering**: 24+ bankruptcy/closure/layoff keywords  
✅ **Database**: SQLite with duplicate prevention  
✅ **UI Dashboard**: Interactive Streamlit interface  
✅ **Sorting**: Newest articles first (by created_at, then published)  
✅ **Clickable Links**: All article headlines link to source URLs  
✅ **Charts**: Timeline, sentiment distribution, source breakdown  
✅ **Filters**: Time range, sentiment range, keyword search  
✅ **Cloud Ready**: Modal deployment configuration complete  

## 🚀 Deploy to Cloud

```bash
# Setup Modal (one-time)
modal setup

# Deploy with auto-updates every 12 hours
modal deploy serve_streamlit.py
```

## 📱 Interface Features

- **Live Metrics**: Total articles, avg sentiment, source count, 24h updates
- **Interactive Charts**: Timeline, sentiment histogram, top sources
- **Smart Filtering**: Time range, sentiment threshold, keyword search  
- **Article Feed**: Chronological list with metadata and full links
- **Responsive Design**: Works on desktop and mobile

## 🔧 Data Sources

- **Reuters Business News**
- **CNN Money & Companies** 
- **Bloomberg Markets**
- **CNBC Finance**
- **MarketWatch Headlines**
- **Fortune Headlines**
- **Wall Street Journal Business**
- **NewsAPI** (optional with API key)

## 💡 Usage Tips

1. **Browse Latest**: Articles auto-sorted newest first
2. **Filter Time**: Use sidebar to adjust date range  
3. **Check Sentiment**: Red = very negative, yellow = mildly negative
4. **Search Keywords**: Find specific topics (e.g., "bankruptcy")
5. **Click Headlines**: Direct links to full articles
6. **Manual Refresh**: Get latest news anytime via sidebar button

---

🤖 **Built with [Memex](https://memex.tech)** - Your negative business news tracker is ready to use!