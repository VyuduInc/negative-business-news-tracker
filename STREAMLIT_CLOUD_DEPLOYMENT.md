# Deploying to Streamlit Cloud

## Prerequisites
1. GitHub account
2. This repository pushed to GitHub
3. Streamlit Cloud account (sign up at https://share.streamlit.io/)

## Deployment Steps

### 1. Push to GitHub
```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Streamlit Cloud deployment"

# Add remote (replace with your GitHub repo URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository
5. Set the main file path to: `app.py`
6. Click "Deploy"

### 3. Configure Secrets (if needed)

If your app uses any API keys or secrets:
1. In Streamlit Cloud dashboard, go to your app settings
2. Click on "Secrets"
3. Add your secrets in TOML format:
   ```toml
   # Example
   API_KEY = "your-api-key-here"
   ```

## Files for Deployment

The following files are required for Streamlit Cloud:

- ✅ `app.py` - Main Streamlit application
- ✅ `requirements.txt` - Python dependencies
- ✅ `packages.txt` - System dependencies (if needed)
- ✅ `.streamlit/config.toml` - Streamlit configuration (optional)
- ✅ `news_collector.py` - Core application logic

## Differences from Modal Deployment

### Modal
- Uses persistent volumes (`/data/`)
- Requires `serve_streamlit.py` wrapper
- Uses `modal deploy` command

### Streamlit Cloud
- Uses ephemeral storage (data resets on rebuild)
- Direct deployment of `app.py`
- Git-based deployment workflow

## Important Notes

⚠️ **Database Persistence**: Streamlit Cloud uses ephemeral storage. The SQLite database (`news_data.db`) will be reset when:
- The app is redeployed
- The app restarts
- Dependencies are updated

If you need persistent storage, consider:
1. Using an external database (PostgreSQL, MongoDB, etc.)
2. Using cloud storage (AWS S3, Google Cloud Storage)
3. Implementing a regular backup strategy

## Monitoring

- View logs in the Streamlit Cloud dashboard
- Monitor app health and usage statistics
- Set up email alerts for deployment failures

## Support

- Streamlit Cloud docs: https://docs.streamlit.io/streamlit-community-cloud
- Community forum: https://discuss.streamlit.io/
