# backend/config.py
# Configuration management for the application

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Google Cloud / Vertex AI
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    _creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Handle relative paths for credentials
    if _creds_path and not os.path.isabs(_creds_path):
        # If relative path, make it relative to project root
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        GOOGLE_APPLICATION_CREDENTIALS = os.path.join(BASE_DIR, _creds_path)
    else:
        GOOGLE_APPLICATION_CREDENTIALS = _creds_path
    
    VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = "cypress-playwright"
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMPLATES_DIR = os.path.join(BASE_DIR, "backend", "templates")
    SESSIONS_DIR = os.path.join(BASE_DIR, "tmp", "sessions")
    UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
    
    # Gemini Model
    GEMINI_MODEL = "gemini-2.5-pro"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.SESSIONS_DIR, exist_ok=True)
        os.makedirs(cls.UPLOADS_DIR, exist_ok=True)

settings = Settings()