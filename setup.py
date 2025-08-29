#!/usr/bin/env python3
"""
Setup script for Negative Business News Tracker
"""
import subprocess
import sys
import os

def run_command(cmd):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running: {cmd}")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"Exception running {cmd}: {e}")
        return False

def setup_environment():
    """Set up the virtual environment and install dependencies"""
    print("🔧 Setting up environment...")
    
    # Create virtual environment
    if not run_command("uv venv"):
        return False
    
    # Install dependencies
    if not run_command("source .venv/bin/activate && uv pip install -r requirements.txt"):
        return False
        
    # Download NLTK data
    if not run_command("source .venv/bin/activate && python -c \"import nltk; nltk.download('punkt'); nltk.download('vader_lexicon')\""):
        return False
        
    # Download TextBlob corpora
    if not run_command("source .venv/bin/activate && python -m textblob.download_corpora"):
        return False
    
    print("✅ Environment setup complete!")
    return True

def collect_initial_data():
    """Collect initial news data"""
    print("📰 Collecting initial news data...")
    if not run_command("source .venv/bin/activate && python news_collector.py"):
        print("⚠️  Failed to collect initial data, but continuing...")
    else:
        print("✅ Initial data collection complete!")

def test_app():
    """Test the Streamlit app"""
    print("🚀 Testing Streamlit app...")
    print("Starting Streamlit on http://localhost:8501")
    print("Press Ctrl+C to stop the app")
    
    try:
        subprocess.run("source .venv/bin/activate && streamlit run app.py --server.headless=true", 
                      shell=True, check=True)
    except KeyboardInterrupt:
        print("\n✅ App test complete!")

if __name__ == "__main__":
    print("🚀 Setting up Negative Business News Tracker")
    print("=" * 50)
    
    if setup_environment():
        collect_initial_data()
        
        print("\n" + "=" * 50)
        print("✅ Setup complete!")
        print("\nNext steps:")
        print("1. Run locally: streamlit run app.py")
        print("2. Deploy to Modal: modal deploy serve_streamlit.py")
        print("3. Optional: Set NEWSAPI_KEY environment variable for more data sources")
        
        # Ask if user wants to test now
        response = input("\nWould you like to test the app now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            test_app()
    else:
        print("❌ Setup failed!")
        sys.exit(1)