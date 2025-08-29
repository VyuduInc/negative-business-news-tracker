import shlex
import subprocess
from pathlib import Path
import modal
import os

# Container setup with dependencies - include source code in image
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "streamlit==1.35.0",
        "feedparser==6.0.11", 
        "requests==2.31.0",
        "nltk==3.8.1",
        "textblob==0.17.1",
        "pandas==2.0.3",
        "plotly==5.15.0",
        "python-dotenv==1.0.0"
    )
    .run_commands(
        "python -c 'import nltk; nltk.download(\"punkt\"); nltk.download(\"vader_lexicon\")'",
        "python -m textblob.download_corpora"
    )
    .add_local_file("app.py", "/root/app.py")
    .add_local_file("news_collector.py", "/root/news_collector.py")
)

app = modal.App(name="negative-business-news", image=image)

# Create volume for persistent data storage
volume = modal.Volume.from_name("news-data", create_if_missing=True)

# Scheduled news update function
@app.function(
    volumes={"/data": volume},
    schedule=modal.Cron("0 */12 * * *")  # Every 12 hours
)
def update_news_scheduled():
    """Scheduled function to update news every 12 hours"""
    import sys
    sys.path.append('/root')
    
    from news_collector import NegativeNewsCollector
    import os
    
    # Use persistent volume for database
    collector = NegativeNewsCollector("/data/news_data.db")
    
    # Get NewsAPI key from environment if available
    newsapi_key = os.environ.get('NEWSAPI_KEY')
    
    saved_count = collector.update_news(newsapi_key)
    print(f"Scheduled update completed. Saved {saved_count} new articles.")
    
    # Commit volume changes
    volume.commit()
    
    return saved_count

# Web server function
@app.function(
    volumes={"/data": volume},
    allow_concurrent_inputs=100,
)
@modal.web_server(8000)
def run():
    """Run the Streamlit application"""
    import sys
    sys.path.append('/root')
    
    # Initialize database if it doesn't exist
    from news_collector import NegativeNewsCollector
    collector = NegativeNewsCollector("/data/news_data.db")
    
    # Run initial data collection if database is empty
    try:
        news_data = collector.get_recent_news(30)
        if not news_data:
            print("Database empty, running initial collection...")
            collector.update_news()
            volume.commit()
    except Exception as e:
        print(f"Initial setup error: {e}")
    
    # Set environment variables for Streamlit
    os.environ['STREAMLIT_BROWSER_GATHERUSAGESTATS'] = 'false'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    
    cmd = f"streamlit run /root/app.py --server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false --server.headless=true"
    subprocess.Popen(shlex.split(cmd))

if __name__ == "__main__":
    app.serve()