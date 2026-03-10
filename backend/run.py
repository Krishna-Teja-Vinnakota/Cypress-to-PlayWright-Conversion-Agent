#!/usr/bin/env python3
"""
run.py - Quick start script for Cypress to Playwright Converter
Run this from the backend directory: python run.py
"""

import sys
import os
import time
import webbrowser
import threading
from pathlib import Path

# Fix import paths - add parent directory to Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Now we can import our modules
try:
    import uvicorn
    from backend.config import settings
    from backend.database.mongodb import db
    from backend.main import app
    print("✅ All modules imported successfully!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you've installed requirements: pip install -r ../requirements.txt")
    sys.exit(1)

def open_browser():
    """Open browser after server starts"""
    # Wait for server to start
    time.sleep(3)
    # Use localhost for browser opening (more user-friendly)
    url = f"http://localhost:{settings.PORT}"
    print(f"🌐 Opening browser: {url}")
    webbrowser.open(url)

def check_dependencies():
    """Check if MongoDB and other dependencies are ready"""
    print("🔍 Checking dependencies...")
    
    # Check if .env file exists
    env_file = parent_dir / ".env"
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("📝 Creating template .env file...")
        
        env_content = """# Google Cloud / Vertex AI Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=gen-lang-client-0375456222-003d04a91a5d.json
VERTEX_AI_LOCATION=us-central1

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/

# Server Configuration
HOST=0.0.0.0
PORT=8000"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("❌ Please update .env with your configuration and run again!")
        return False
    
    # Check if required directories exist
    settings.ensure_directories()
    
    # Check template directories
    templates_dir = parent_dir / "backend" / "templates"
    required_templates = ["cypress-js", "cypress-ts", "playwright-js", "playwright-ts"]
    
    for template in required_templates:
        template_path = templates_dir / template / "node_modules"
        if not template_path.exists():
            print(f"⚠️  {template} node_modules not found!")
            print(f"💡 Run: cd {templates_dir / template} && npm install")
    
    print("✅ Dependencies check complete!")
    return True

def main():
    """Main function to start the application"""
    print("🚀 Starting Cypress to Playwright Converter...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Print startup info
    print(f"🖥️  Backend: http://localhost:{settings.PORT}")
    print(f"🎨 Frontend: http://localhost:{settings.PORT}")
    print(f"📊 API Docs: http://localhost:{settings.PORT}/docs")
    print(f"🔍 Health Check: http://localhost:{settings.PORT}/health")
    print("=" * 50)
    print(f"🚀 Starting at: http://localhost:{settings.PORT}/")
    print("=" * 50)
    
    # Start browser opening in background
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the server
    try:
        print("🔥 Starting FastAPI server...")
        print("💡 Press Ctrl+C to stop the server")
        print("")
        
        uvicorn.run(
            "backend.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Make sure MongoDB is running and .env is configured correctly")

if __name__ == "__main__":
    main()