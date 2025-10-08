# Business News Negative Tracker - Deployment Guide

## 🚀 Streamlit Cloud Deployment (Recommended)

### Prerequisites
- GitHub account
- Streamlit Cloud account (free at https://share.streamlit.io/)
- Repository: `VyuduInc/negative-business-news-tracker`

### Quick Deploy Steps

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io/
   - Sign in with your GitHub account

2. **Create New App**
   - Click "New app"
   - Repository: `VyuduInc/negative-business-news-tracker`
   - Branch: `main`
   - Main file path: `app.py`
   - Click "Deploy"

3. **Wait for Deployment**
   - Initial deployment: ~1-2 minutes
   - App will be available at: `https://[your-app-name].streamlit.app`

4. **First Time Setup**
   - App will show empty state
   - Click "🔄 Update News" in sidebar
   - Wait 2-3 minutes for initial data collection
   - Refresh page to see articles

### Configuration Files

The following files are optimized for Streamlit Cloud:

- ✅ `requirements.txt` - Python dependencies (Python 3.11 compatible)
- ✅ `packages.txt` - System dependencies (empty, none needed)
- ✅ `.python-version` - Specifies Python 3.11 for compatibility
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `app.py` - Main application

### Python Version

**Important:** This app requires Python 3.11 (not 3.13) due to pandas compatibility.

The `.python-version` file ensures Streamlit Cloud uses Python 3.11.

### Dependencies

All dependencies are pinned with flexible version ranges for compatibility:

```txt
streamlit>=1.35.0,<2.0.0
feedparser>=6.0.11
requests>=2.31.0
nltk>=3.8.1
textblob>=0.17.1
pandas>=2.1.0         # Compatible with Python 3.11+
plotly>=5.15.0
python-dotenv>=1.0.0
```

### Performance Optimizations

1. **Lazy Loading**: News collection only happens when user clicks button
2. **Data Caching**: News data cached for 30 minutes (`@st.cache_data`)
3. **Resource Caching**: Collector and NLTK data cached (`@st.cache_resource`)
4. **Efficient Database**: SQLite with indexed queries

### Common Issues & Solutions

#### Issue: "Error installing requirements"
**Solution:** Ensure Python 3.11 is being used. The `.python-version` file should handle this.

#### Issue: "App takes too long to start"
**Solution:** This is expected on first deployment. The app downloads NLTK data once. Subsequent starts are fast.

#### Issue: "No data showing"
**Solution:** Click "🔄 Update News" button in sidebar to collect articles.

#### Issue: "Database resets on reboot"
**Solution:** This is expected behavior on Streamlit Cloud (ephemeral storage). For persistent storage, consider:
- External database (PostgreSQL, MongoDB)
- Cloud storage (S3, Google Cloud Storage)
- Regular data exports

### Environment Variables (Optional)

If you want to use NewsAPI for enhanced collection:

1. Get API key from https://newsapi.org/ (free tier available)
2. In Streamlit Cloud dashboard:
   - Go to app settings
   - Click "Secrets"
   - Add:
   ```toml
   NEWSAPI_KEY = "your_api_key_here"
   ```

### Monitoring

- View logs in Streamlit Cloud dashboard
- Monitor app health and usage
- Set up email alerts for failures

### Reboot App

If app needs restart:
1. Go to Streamlit Cloud dashboard
2. Click "Manage app"
3. Click "Reboot app"

### Update Code

To deploy changes:
1. Push code to GitHub `main` branch
2. Streamlit Cloud auto-deploys (takes 1-2 min)
3. Or manually reboot in dashboard

---

## 🔧 Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/VyuduInc/negative-business-news-tracker.git
cd negative-business-news-tracker

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Run app
streamlit run app.py --server.headless=true
```

### Local Database

Database file: `news_data.db` (created automatically)

---

## 📊 Features

- ✅ Real-time negative business news monitoring
- ✅ 50+ RSS news sources
- ✅ Sentiment analysis
- ✅ Crisis category filtering
- ✅ Time range filtering
- ✅ Keyword search
- ✅ Interactive visualizations
- ✅ Article metadata and links

---

## 🛟 Support

- Streamlit Docs: https://docs.streamlit.io/
- Community Forum: https://discuss.streamlit.io/
- GitHub Issues: https://github.com/VyuduInc/negative-business-news-tracker/issues
