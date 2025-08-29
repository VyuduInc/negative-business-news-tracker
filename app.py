import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from news_collector import NegativeNewsCollector
import os

# Page configuration
st.set_page_config(
    page_title="Negative Business News Tracker",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize news collector
@st.cache_resource
def get_news_collector():
    return NegativeNewsCollector()

collector = get_news_collector()

# App header
st.title("📉 Negative Business News Tracker")
st.markdown("*Tracking business failures, closures, bankruptcies, and other negative corporate news*")

# Sidebar controls
st.sidebar.header("Filter Options")

# Time range filter
time_options = {
    "Last 24 hours": 1,
    "Last 3 days": 3,
    "Last week": 7,
    "Last 2 weeks": 14,
    "Last month": 30
}

selected_time = st.sidebar.selectbox("Time Range", list(time_options.keys()), index=2)
days = time_options[selected_time]

# Sentiment filter
sentiment_range = st.sidebar.slider(
    "Sentiment Score Range (more negative ← → less negative)", 
    -1.0, 1.0, (-1.0, 0.2), step=0.1
)

# Keyword filter
keyword_filter = st.sidebar.text_input("Filter by keyword (optional)")

# Manual refresh button
if st.sidebar.button("🔄 Refresh News Data"):
    with st.spinner("Fetching latest news..."):
        try:
            # Try to get NewsAPI key from secrets or environment
            newsapi_key = None
            try:
                newsapi_key = st.secrets.get("NEWSAPI_KEY", os.getenv("NEWSAPI_KEY"))
            except:
                newsapi_key = os.getenv("NEWSAPI_KEY")
            
            saved_count = collector.update_news(newsapi_key)
            st.sidebar.success(f"Updated! Found {saved_count} new articles")
            st.rerun()  # Refresh the page to show new data
        except Exception as e:
            st.sidebar.error(f"Update failed: {e}")

# Get news data
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_news_data(days_back):
    return collector.get_recent_news(days_back)

# Load data
news_data = load_news_data(days)

if not news_data:
    st.warning("No negative business news found for the selected time period. Try expanding the time range or refreshing the data.")
    # Initialize with some sample data if database is empty
    with st.spinner("Initializing with latest news..."):
        try:
            newsapi_key = None
            try:
                newsapi_key = st.secrets.get("NEWSAPI_KEY", os.getenv("NEWSAPI_KEY"))
            except:
                newsapi_key = os.getenv("NEWSAPI_KEY")
            
            saved_count = collector.update_news(newsapi_key)
            if saved_count > 0:
                st.success(f"Initialized with {saved_count} articles!")
                st.rerun()
            else:
                st.info("No negative business news found in recent feeds. Check back later or try refreshing.")
        except Exception as e:
            st.error(f"Failed to initialize data: {e}")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(news_data)
df['created_at'] = pd.to_datetime(df['created_at'])
df['published'] = pd.to_datetime(df['published'], errors='coerce')

# Apply filters
if sentiment_range:
    df = df[(df['sentiment_score'] >= sentiment_range[0]) & 
            (df['sentiment_score'] <= sentiment_range[1])]

if keyword_filter:
    mask = df.apply(lambda row: keyword_filter.lower() in row.astype(str).str.lower().str.cat(sep=' '), axis=1)
    df = df[mask]

# Sort by newest to oldest (created_at first, then published)
df = df.sort_values(['created_at', 'published'], ascending=[False, False])

# Main content
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Articles", len(df))

with col2:
    avg_sentiment = df['sentiment_score'].mean() if len(df) > 0 else 0
    st.metric("Avg Sentiment", f"{avg_sentiment:.3f}")

with col3:
    sources_count = df['source'].nunique() if len(df) > 0 else 0
    st.metric("News Sources", sources_count)

with col4:
    recent_articles = len(df[df['created_at'] >= datetime.now() - timedelta(hours=24)])
    st.metric("Last 24h", recent_articles)

# Charts
if len(df) > 0:
    # Timeline chart
    st.subheader("📈 News Timeline")
    
    # Group by date
    df['date'] = df['created_at'].dt.date
    timeline_data = df.groupby('date').size().reset_index(name='count')
    
    if len(timeline_data) > 1:
        fig_timeline = px.line(timeline_data, x='date', y='count', 
                             title="Negative Business News Articles Over Time")
        fig_timeline.update_layout(height=400)
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Sentiment distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("😡 Sentiment Distribution")
        fig_sentiment = px.histogram(df, x='sentiment_score', bins=20, 
                                   title="Distribution of Sentiment Scores")
        fig_sentiment.update_layout(height=400)
        st.plotly_chart(fig_sentiment, use_container_width=True)
    
    with col2:
        st.subheader("📰 Sources")
        source_counts = df['source'].value_counts().head(10)
        fig_sources = px.bar(x=source_counts.values, y=source_counts.index, 
                           orientation='h', title="Top News Sources")
        fig_sources.update_layout(height=400)
        st.plotly_chart(fig_sources, use_container_width=True)

# News articles list
st.subheader("📋 Latest Negative Business News")
st.markdown(f"*Showing {len(df)} articles sorted by newest first*")

# Display articles (already sorted by newest to oldest)
for idx, article in df.iterrows():
    with st.container():
        # Title with clickable link
        if article['link']:
            st.markdown(f"### 📉 [{article['title']}]({article['link']})")
        else:
            st.markdown(f"### 📉 {article['title']}")
        
        # Article metadata in columns
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        
        with col1:
            st.write(f"**Source:** {article['source']}")
            
        with col2:
            if pd.notna(article['published']):
                pub_date = pd.to_datetime(article['published']).strftime('%Y-%m-%d %H:%M')
                st.write(f"**Published:** {pub_date}")
            
        with col3:
            sentiment_color = "🔴" if article['sentiment_score'] < -0.2 else "🟡" if article['sentiment_score'] < 0 else "🟢"
            st.write(f"**Sentiment:** {sentiment_color} {article['sentiment_score']:.3f}")
            
        with col4:
            if article['negative_keywords']:
                keywords = article['negative_keywords'].split(',')
                keyword_badges = ' '.join([f"`{k.strip()}`" for k in keywords[:3]])
                st.markdown(f"**Keywords:** {keyword_badges}")
        
        # Article description
        if article['description']:
            st.write(article['description'])
        
        # Read full article button
        if article['link']:
            st.markdown(f"[📖 **Read Full Article**]({article['link']}) ↗️")
        
        st.divider()

# Footer
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **Data Sources:**
    - RSS feeds: Reuters, CNN, Bloomberg, CNBC, MarketWatch, Fortune, WSJ
    - NewsAPI for additional coverage
    """)

with col2:
    st.markdown("""
    **Auto-Updates:**
    - Scheduled updates every 12 hours when deployed
    - Use sidebar refresh for manual updates
    """)

st.info("💡 **Note:** Articles are filtered for negative business sentiment using keyword matching and sentiment analysis. All links are clickable and will open in a new tab.")

# Debug info (only show in development)
if os.getenv('DEBUG', '').lower() == 'true':
    with st.expander("Debug Info"):
        st.write(f"Database path: {collector.db_path}")
        st.write(f"Total articles in database: {len(news_data)}")
        st.write(f"Filtered articles shown: {len(df)}")
        st.write(f"Sentiment range: {sentiment_range}")
        if keyword_filter:
            st.write(f"Keyword filter: '{keyword_filter}'")