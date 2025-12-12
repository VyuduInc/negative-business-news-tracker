import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from news_collector import NegativeNewsCollector
import os
import time
import threading

# Download NLTK data on first run (needed for TextBlob)
import nltk
import ssl

# Handle SSL certificate issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data
@st.cache_resource
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
    return True

download_nltk_data()

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
    # Use local database path
    db_path = "news_data.db"
    return NegativeNewsCollector(db_path)

collector = get_news_collector()

# Modern 2025 color scheme - CSS variables
st.markdown("""
<style>
    :root {
        --bg-dark: #2c2c2e;
        --surface-dark: #3a3a3c;
        --text-primary: #f5f5f7;
        --text-secondary: #a8a8a8;
        --accent-primary: #00d4aa;
        --alert-warm: #ff9f43;
        --alert-critical: #ee5a6f;
    }
</style>
<div style="background: linear-gradient(135deg, #2c2c2e 0%, #3a3a3c 100%); padding: 2rem; border-radius: 16px; margin-bottom: 2rem; border: 1px solid rgba(168, 168, 168, 0.1);">
    <h1 style="color: #f5f5f7; margin: 0; font-size: 2.5rem; font-weight: 600;">📉 Business Crisis Monitor</h1>
    <p style="color: #a8a8a8; margin: 0.75rem 0 0 0; font-size: 1.1rem;">Real-time tracking of bankruptcies, closures, layoffs & corporate failures</p>
</div>
""", unsafe_allow_html=True)

# Sidebar controls with news-style branding
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
    <h3 style="color: white; margin: 0; text-align: center;">📊 News Filters</h3>
</div>
""", unsafe_allow_html=True)

# Crisis categories with "All" option
st.sidebar.markdown("**📊 Crisis Categories**")
all_crisis_types = ["bankruptcy", "closure", "layoffs", "losses", "restructuring", "liquidation", "investigation", "lawsuit", "fraud", "decline", "struggling"]

crisis_filter_mode = st.sidebar.radio(
    "Crisis Filter Mode:",
    ["All Categories", "Specific Categories"],
    index=0
)

if crisis_filter_mode == "Specific Categories":
    crisis_types = st.sidebar.multiselect(
        "Select crisis types:",
        all_crisis_types,
        default=[]
    )
else:
    crisis_types = []  # Empty means show all

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

st.sidebar.markdown("**⚡ Real-time Mode**")
st.sidebar.write(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

# Simple auto-refresh with meta tag
auto_refresh = st.sidebar.selectbox(
    "Auto-refresh interval:",
    ["Off", "5 minutes", "10 minutes", "30 minutes"],
    index=0
)

if auto_refresh != "Off":
    refresh_seconds = {
        "5 minutes": 300,
        "10 minutes": 600, 
        "30 minutes": 1800
    }[auto_refresh]
    
    st.markdown(f'<meta http-equiv="refresh" content="{refresh_seconds}">', unsafe_allow_html=True)
    st.sidebar.success(f"🔄 Auto-refresh every {auto_refresh}")

# Manual refresh button
if st.sidebar.button("🔄 Refresh News Data"):
    with st.spinner("Fetching latest news..."):
        try:
            # Quick update using standard collector
            newsapi_key = os.getenv("NEWSAPI_KEY")
            saved_count = collector.update_news(newsapi_key)
            st.sidebar.success(f"Updated! Found {saved_count} new articles")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Update failed: {e}")

if st.sidebar.button("⚡ Fast Update (Local Sources)"):
    with st.spinner("Quick local news scan..."):
        try:
            from fast_collector import FastNewsCollector
            fast_collector = FastNewsCollector(collector.db_path) 
            saved_count, total_collected, elapsed_time = fast_collector.fast_update(target_articles=30)
            st.sidebar.success(f"⚡ {saved_count} new articles in {elapsed_time:.1f}s")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Fast update failed: {e}")

# Get news data
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_news_data(days_back):
    return collector.get_recent_news(days_back)

# Load data
news_data = load_news_data(days)

if not news_data:
    st.warning("📭 No negative business news found for the selected time period.")
    st.info("👉 **First time setup:** Use the sidebar button '🔄 Update News' to collect initial articles (takes ~2-3 minutes)")
    st.info("Try expanding the time range or click the update button to refresh data.")
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

# Apply crisis type filter (only if specific categories selected)
if crisis_filter_mode == "Specific Categories" and crisis_types:
    crisis_mask = df['negative_keywords'].str.lower().str.contains('|'.join(crisis_types), case=False, na=False)
    df = df[crisis_mask]

# Sort by newest to oldest (created_at first, then published)
df = df.sort_values(['created_at', 'published'], ascending=[False, False])

# Separate LinkedIn trending articles
linkedin_df = df[df['source'] == 'LinkedIn Trending'].head(10)
regular_df = df[df['source'] != 'LinkedIn Trending']

# Modern metrics dashboard with 2025 colors
st.markdown("""
<div style="background: #3a3a3c; padding: 1.5rem; border-radius: 12px; margin: 1.5rem 0; border: 1px solid rgba(168, 168, 168, 0.1);">
    <h3 style="color: #f5f5f7; margin: 0; font-size: 1.5rem;">📊 Crisis Dashboard</h3>
    <p style="color: #a8a8a8; margin: 0.5rem 0 0 0; font-size: 0.95rem;">Real-time monitoring across 40+ national & local sources</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("🚨 Crisis Alerts", len(df))

with col2:
    avg_sentiment = df['sentiment_score'].mean() if len(df) > 0 else 0
    severity = "HIGH" if avg_sentiment < -0.1 else "MEDIUM" if avg_sentiment < 0.05 else "LOW"
    st.metric("⚡ Crisis Severity", severity)

with col3:
    sources_count = df['source'].nunique() if len(df) > 0 else 0
    st.metric("📰 News Sources", sources_count)

with col4:
    recent_articles = len(df[df['created_at'] >= datetime.now() - timedelta(hours=24)]) if len(df) > 0 else 0
    st.metric("🕒 Last 24 Hours", recent_articles)

with col5:
    linkedin_count = len(linkedin_df)
    st.metric("🔗 LinkedIn Trending", linkedin_count)

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

# LinkedIn trending section with modern styling
if len(linkedin_df) > 0:
    st.markdown("""
    <div style="background: #3a3a3c; padding: 1rem; border-radius: 12px; margin: 1rem 0; border-left: 4px solid #00d4aa;">
        <h3 style="color: #f5f5f7; margin: 0; font-size: 1.3rem;">🔗 Trending LinkedIn Discussions</h3>
        <p style="color: #a8a8a8; margin: 0.5rem 0 0 0; font-size: 0.9rem;">Most shared crisis discussions (24h)</p>
    </div>
    """, unsafe_allow_html=True)
    
    for idx, article in linkedin_df.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**[{article['title']}]({article['link']})** 📈")
            st.markdown(f"*{article['description']}*")
        with col2:
            st.markdown("🔥 **Trending**")
            st.markdown(f"`{article['negative_keywords']}`")
        st.markdown("---")

# Main news articles list with modern header
st.markdown("""
<div style="background: #3a3a3c; padding: 1.25rem; border-radius: 12px; margin: 1.5rem 0; border-left: 4px solid #ee5a6f;">
    <h3 style="color: #f5f5f7; margin: 0; font-size: 1.4rem;">🚨 Breaking Corporate Crisis News</h3>
    <p style="color: #a8a8a8; margin: 0.5rem 0 0 0; font-size: 0.95rem;">Latest bankruptcies, closures, and business failures</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="color: #a8a8a8; margin: 0.5rem 0 1rem 0; font-size: 0.9rem;">
    <strong style="color: #00d4aa;">{len(regular_df)}</strong> crisis alerts from <strong style="color: #00d4aa;">{regular_df['source'].nunique()}</strong> sources • Sorted by newest first
</div>
""", unsafe_allow_html=True)

# Display articles in news aggregator style (using regular_df to exclude LinkedIn trending)
for idx, article in regular_df.iterrows():
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
    
    # Modern 2025 news card styling
    sentiment_color = "#ee5a6f" if article['sentiment_score'] < -0.2 else "#ff9f43" if article['sentiment_score'] < 0 else "#a8a8a8"
    severity_label = "SEVERE" if article['sentiment_score'] < -0.2 else "MODERATE" if article['sentiment_score'] < 0 else "MILD"
    
    st.markdown(f"""
    <div style="border-left: 4px solid {sentiment_color}; background: #3a3a3c; padding: 1.5rem; margin: 1rem 0; border-radius: 0 12px 12px 0; border: 1px solid rgba(168, 168, 168, 0.1);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <span style="background: {sentiment_color}; color: #f5f5f7; padding: 0.3rem 0.6rem; border-radius: 8px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px;">{severity_label}</span>
            <span style="color: #a8a8a8; font-size: 0.85rem;">{time_ago}</span>
        </div>
        <h3 style="margin: 0.5rem 0; font-size: 1.35rem; line-height: 1.4;"><a href="{article['link']}" target="_blank" style="color: #f5f5f7; text-decoration: none; transition: color 0.2s;" onmouseover="this.style.color='#00d4aa'" onmouseout="this.style.color='#f5f5f7'">{article['title']}</a></h3>
        <div style="color: #a8a8a8; font-size: 0.9rem; margin: 0.75rem 0 0 0;">
            <strong style="color: #00d4aa;">{article['source']}</strong> • {pd.to_datetime(article['published']).strftime('%B %d, %Y at %I:%M %p') if pd.notna(article['published']) else 'Recently published'}
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
                st.markdown(f'<span style="background: rgba(238, 90, 111, 0.15); color: #ee5a6f; padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.8rem; margin: 0.2rem; display: inline-block; border: 1px solid rgba(238, 90, 111, 0.3);">{keyword.strip()}</span>', unsafe_allow_html=True)
    
    # Modern read more button with accent color
    if article['link']:
        st.markdown(f"""
        <a href="{article['link']}" target="_blank" style="
            background: #00d4aa;
            color: #2c2c2e;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 600;
            display: inline-block;
            margin: 0.75rem 0 0.5rem 0;
            transition: all 0.2s;
        " onmouseover="this.style.background='#00f5c4'; this.style.transform='translateY(-1px)'" onmouseout="this.style.background='#00d4aa'; this.style.transform='translateY(0)'">📖 Read Full Story →</a>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

# Professional news footer
st.markdown("---")

# Use columns instead of HTML grid for better compatibility
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📊 Data Sources**")
    st.write("Reuters • Bloomberg • CNN • CNBC • MarketWatch • Fortune • WSJ • Yahoo Finance • Associated Press • Financial Times • Business Insider")

with col2:
    st.markdown("**🔄 Updates**") 
    st.write("Real-time monitoring • Auto-refresh every 12 hours • LinkedIn trending integration")

with col3:
    st.markdown("**🎯 Coverage**")
    st.write("Bankruptcies • Closures • Layoffs • Financial crises • Corporate restructuring")

st.info("⚡ Powered by advanced sentiment analysis and real-time RSS monitoring • All articles link directly to original sources")

# Debug info (only show in development)
if os.getenv('DEBUG', '').lower() == 'true':
    with st.expander("Debug Info"):
        st.write(f"Database path: {collector.db_path}")
        st.write(f"Total articles in database: {len(news_data)}")
        st.write(f"Filtered articles shown: {len(df)}")
        st.write(f"Sentiment range: {sentiment_range}")
        if keyword_filter:
            st.write(f"Keyword filter: '{keyword_filter}'")