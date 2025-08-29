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
    # Use persistent volume path if available (Modal deployment)
    db_path = "/data/news_data.db" if os.path.exists("/data") else "news_data.db"
    return NegativeNewsCollector(db_path)

collector = get_news_collector()

# App header with news aggregator styling
st.markdown("""
<div style="background: linear-gradient(90deg, #FF6B6B 0%, #FF8E53 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
    <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: bold;">📉 Business Crisis Monitor</h1>
    <p style="color: white; margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Breaking news on bankruptcies, closures, layoffs & corporate failures</p>
</div>
""", unsafe_allow_html=True)

# Sidebar controls with news-style branding
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
    <h3 style="color: white; margin: 0; text-align: center;">📊 News Filters</h3>
</div>
""", unsafe_allow_html=True)

# Crisis categories
st.sidebar.markdown("**📊 Crisis Categories**")
crisis_types = st.sidebar.multiselect(
    "Filter by crisis type:",
    ["bankruptcy", "closure", "layoffs", "losses", "restructuring", "liquidation"],
    default=[]
)

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

# Apply crisis type filter
if crisis_types:
    crisis_mask = df['negative_keywords'].str.lower().str.contains('|'.join(crisis_types), case=False, na=False)
    df = df[crisis_mask]

# Sort by newest to oldest (created_at first, then published)
df = df.sort_values(['created_at', 'published'], ascending=[False, False])

# News-style metrics dashboard
st.markdown("""
<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
    <h3 style="color: white; margin: 0; text-align: center;">📊 CRISIS DASHBOARD</h3>
    <p style="color: white; margin: 0.5rem 0 0 0; text-align: center; opacity: 0.9;">Real-time business failure monitoring</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="color: #e74c3c; margin: 0; font-size: 2rem;">{}</h2>
        <p style="color: #7f8c8d; margin: 0.5rem 0 0 0;">Crisis Alerts</p>
    </div>
    """.format(len(df)), unsafe_allow_html=True)

with col2:
    avg_sentiment = df['sentiment_score'].mean() if len(df) > 0 else 0
    severity = "HIGH" if avg_sentiment < -0.1 else "MEDIUM" if avg_sentiment < 0.05 else "LOW"
    color = "#e74c3c" if avg_sentiment < -0.1 else "#f39c12" if avg_sentiment < 0.05 else "#27ae60"
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="color: {}; margin: 0; font-size: 1.5rem;">{}</h2>
        <p style="color: #7f8c8d; margin: 0.5rem 0 0 0;">Crisis Severity</p>
    </div>
    """.format(color, severity), unsafe_allow_html=True)

with col3:
    sources_count = df['source'].nunique() if len(df) > 0 else 0
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="color: #3498db; margin: 0; font-size: 2rem;">{}</h2>
        <p style="color: #7f8c8d; margin: 0.5rem 0 0 0;">News Sources</p>
    </div>
    """.format(sources_count), unsafe_allow_html=True)

with col4:
    recent_articles = len(df[df['created_at'] >= datetime.now() - timedelta(hours=24)]) if len(df) > 0 else 0
    st.markdown("""
    <div style="background: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="color: #9b59b6; margin: 0; font-size: 2rem;">{}</h2>
        <p style="color: #7f8c8d; margin: 0.5rem 0 0 0;">Last 24 Hours</p>
    </div>
    """.format(recent_articles), unsafe_allow_html=True)

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
        fig_sentiment = px.histogram(df, x='sentiment_score', nbins=20, 
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

# News articles list - styled like a news aggregator
st.markdown("""
<div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
    <h2 style="color: #2c3e50; margin: 0; font-size: 1.8rem;">🚨 BREAKING: Corporate Crisis News</h2>
    <p style="color: #7f8c8d; margin: 0.5rem 0 0 0;">Latest bankruptcies, closures, and business failures • Updated continuously</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**{len(df)} crisis alerts** • Sorted by most recent")

# Display articles in news aggregator style
for idx, article in df.iterrows():
    # Parse dates for better display
    try:
        pub_date = pd.to_datetime(article['published']) if pd.notna(article['published']) else None
        time_ago = ""
        if pub_date:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            diff = now - pub_date
            if diff.days > 0:
                time_ago = f"{diff.days}d ago"
            elif diff.seconds > 3600:
                time_ago = f"{diff.seconds // 3600}h ago"
            else:
                time_ago = f"{diff.seconds // 60}m ago"
    except:
        time_ago = ""
    
    # News card styling
    sentiment_color = "#dc3545" if article['sentiment_score'] < -0.2 else "#fd7e14" if article['sentiment_score'] < 0 else "#6c757d"
    severity_label = "SEVERE" if article['sentiment_score'] < -0.2 else "MODERATE" if article['sentiment_score'] < 0 else "MILD"
    
    st.markdown(f"""
    <div style="border-left: 4px solid {sentiment_color}; background: white; padding: 1.5rem; margin: 1rem 0; border-radius: 0 8px 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <span style="background: {sentiment_color}; color: white; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem; font-weight: bold;">{severity_label} CRISIS</span>
            <span style="color: #6c757d; font-size: 0.85rem;">{time_ago}</span>
        </div>
        <h3 style="margin: 0.5rem 0; font-size: 1.4rem; line-height: 1.3;"><a href="{article['link']}" target="_blank" style="color: #2c3e50; text-decoration: none;">{article['title']}</a></h3>
        <div style="color: #6c757d; font-size: 0.9rem; margin: 0.5rem 0;">
            <strong>{article['source']}</strong> • {pd.to_datetime(article['published']).strftime('%B %d, %Y at %I:%M %p') if pd.notna(article['published']) else 'Recently published'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Article preview and keywords
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if article['description']:
            # Truncate description for cleaner look
            desc = article['description'][:200] + "..." if len(article['description']) > 200 else article['description']
            st.markdown(f"*{desc}*")
    
    with col2:
        if article['negative_keywords']:
            keywords = article['negative_keywords'].split(',')[:3]
            for keyword in keywords:
                st.markdown(f'<span style="background: #ffe6e6; color: #d63031; padding: 0.2rem 0.4rem; border-radius: 6px; font-size: 0.8rem; margin: 0.1rem; display: inline-block;">{keyword.strip()}</span>', unsafe_allow_html=True)
    
    # Read more button
    if article['link']:
        st.markdown(f"""
        <a href="{article['link']}" target="_blank" style="
            background: linear-gradient(90deg, #FF6B6B 0%, #FF8E53 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: bold;
            display: inline-block;
            margin: 0.5rem 0;
        ">📖 Read Full Story →</a>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

# Professional news footer
st.markdown("---")
st.markdown("""
<div style="background: #2c3e50; color: white; padding: 2rem; border-radius: 10px; margin: 2rem 0;">
    <div style="text-align: center; margin-bottom: 1rem;">
        <h4 style="margin: 0; color: #ecf0f1;">📰 Business Crisis Monitor</h4>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">Professional business intelligence for corporate failures</p>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 1.5rem;">
        <div>
            <h5 style="color: #3498db; margin: 0 0 0.5rem 0;">📊 Data Sources</h5>
            <p style="font-size: 0.9rem; opacity: 0.8; margin: 0;">Reuters • Bloomberg • CNN • CNBC<br/>MarketWatch • Fortune • WSJ</p>
        </div>
        <div>
            <h5 style="color: #e74c3c; margin: 0 0 0.5rem 0;">🔄 Updates</h5>
            <p style="font-size: 0.9rem; opacity: 0.8; margin: 0;">Real-time monitoring<br/>Auto-refresh every 12 hours</p>
        </div>
        <div>
            <h5 style="color: #f39c12; margin: 0 0 0.5rem 0;">🎯 Coverage</h5>
            <p style="font-size: 0.9rem; opacity: 0.8; margin: 0;">Bankruptcies • Closures<br/>Layoffs • Financial crises</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; padding: 1rem; color: #7f8c8d;">
    <p style="margin: 0;">⚡ Powered by advanced sentiment analysis and real-time RSS monitoring • All articles link directly to original sources</p>
</div>
""", unsafe_allow_html=True)

# Debug info (only show in development)
if os.getenv('DEBUG', '').lower() == 'true':
    with st.expander("Debug Info"):
        st.write(f"Database path: {collector.db_path}")
        st.write(f"Total articles in database: {len(news_data)}")
        st.write(f"Filtered articles shown: {len(df)}")
        st.write(f"Sentiment range: {sentiment_range}")
        if keyword_filter:
            st.write(f"Keyword filter: '{keyword_filter}'")