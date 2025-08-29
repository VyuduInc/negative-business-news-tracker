import shlex
import subprocess
from pathlib import Path
import modal
import os

# Container setup with dependencies
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "streamlit==1.35.0",
    "feedparser==6.0.11", 
    "requests==2.31.0",
    "nltk==3.8.1",
    "textblob==0.17.1",
    "pandas==2.0.3",
    "plotly==5.15.0",
    "python-dotenv==1.0.0"
).run_commands(
    "python -c 'import nltk; nltk.download(\"punkt\"); nltk.download(\"vader_lexicon\")'",
    "python -m textblob.download_corpora"
)

app = modal.App(name="negative-business-news", image=image)

# Mount all necessary files
files_to_mount = [
    ("app.py", "/root/app.py"),
    ("news_collector.py", "/root/news_collector.py"),
]

mounts = []
for local_file, remote_path in files_to_mount:
    local_path = Path(__file__).parent / local_file
    if local_path.exists():
        mounts.append(modal.Mount.from_local_file(local_path, Path(remote_path)))

# Scheduled news update function
@app.function(
    mounts=mounts,
    schedule=modal.Cron("0 */12 * * *")  # Every 12 hours
)
def update_news_scheduled():
    """Scheduled function to update news every 12 hours"""
    import sys
    sys.path.append('/root')
    
    from news_collector import NegativeNewsCollector
    import os
    
    collector = NegativeNewsCollector("/tmp/news_data.db")
    
    # Get NewsAPI key from environment if available
    newsapi_key = os.environ.get('NEWSAPI_KEY')
    
    saved_count = collector.update_news(newsapi_key)
    print(f"Scheduled update completed. Saved {saved_count} new articles.")
    
    return saved_count

# Web server function
@app.function(
    allow_concurrent_inputs=100,
    mounts=mounts,
)
@modal.web_server(8000)
def run():
    """Run the Streamlit application"""
    cmd = f"streamlit run /root/app.py --server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false --server.headless=true"
    subprocess.Popen(shlex.split(cmd))

if __name__ == "__main__":
    app.serve()