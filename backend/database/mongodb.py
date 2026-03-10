# backend/database/mongodb.py
# MongoDB connection and database operations

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, List, Any
from datetime import datetime
from backend.config import settings

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB"""
        cls.client = AsyncIOMotorClient(settings.MONGO_URI)
        cls.db = cls.client[settings.MONGO_DB_NAME]
        print(f"✅ Connected to MongoDB: {settings.MONGO_DB_NAME}")
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls.client:
            cls.client.close()
            print("❌ Disconnected from MongoDB")
    
    @classmethod
    def get_collection(cls, name: str):
        """Get a collection by name"""
        return cls.db[name]
    
    # ===== SESSION OPERATIONS =====
    
    @classmethod
    async def create_session(cls, session_data: Dict) -> str:
        """Create a new session"""
        collection = cls.get_collection("sessions")
        result = await collection.insert_one(session_data)
        return str(result.inserted_id)
    
    @classmethod
    async def get_session(cls, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        collection = cls.get_collection("sessions")
        return await collection.find_one({"session_id": session_id})
    
    @classmethod
    async def update_session(cls, session_id: str, update_data: Dict):
        """Update session data"""
        collection = cls.get_collection("sessions")
        await collection.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
    
    @classmethod
    async def get_last_session(cls) -> Optional[Dict]:
        """Get the most recent session"""
        collection = cls.get_collection("sessions")
        cursor = collection.find().sort("created_at", -1).limit(1)
        sessions = await cursor.to_list(length=1)
        return sessions[0] if sessions else None
    
    @classmethod
    async def add_file_version(cls, session_id: str, file_id: str, version_data: Dict):
        """Add a new version to a file's playwright_versions array"""
        collection = cls.get_collection("sessions")
        await collection.update_one(
            {"session_id": session_id, "files.file_id": file_id},
            {
                "$push": {"files.$.playwright_versions": version_data},
                "$inc": {"files.$.current_version": 1}
            }
        )
    
    @classmethod
    async def set_approved_version(cls, session_id: str, file_id: str, version: int):
        """Set the approved version for a file"""
        collection = cls.get_collection("sessions")
        await collection.update_one(
            {"session_id": session_id, "files.file_id": file_id},
            {"$set": {"files.$.approved_version": version}}
        )
    
    @classmethod
    async def get_file_data(cls, session_id: str, file_id: str) -> Optional[Dict]:
        """Get specific file data from session"""
        session = await cls.get_session(session_id)
        if session and "files" in session:
            for file in session["files"]:
                if file["file_id"] == file_id:
                    return file
        return None
    
    # ===== RESULTS OPERATIONS =====
    
    @classmethod
    async def save_cypress_results(cls, results_data: Dict):
        """Save Cypress test results"""
        collection = cls.get_collection("cypress_results")
        await collection.insert_one(results_data)
    
    @classmethod
    async def save_playwright_results(cls, results_data: Dict):
        """Save Playwright test results"""
        collection = cls.get_collection("playwright_results")
        await collection.insert_one(results_data)
    
    @classmethod
    async def get_cypress_results(cls, session_id: str) -> Optional[Dict]:
        """Get Cypress results for a session"""
        collection = cls.get_collection("cypress_results")
        return await collection.find_one({"session_id": session_id})
    
    @classmethod
    async def get_playwright_results(cls, session_id: str) -> Optional[Dict]:
        """Get Playwright results for a session"""
        collection = cls.get_collection("playwright_results")
        return await collection.find_one({"session_id": session_id})
    
    @classmethod
    async def save_comparison_results(cls, comparison_data: Dict):
        """Save comparison results"""
        collection = cls.get_collection("comparison_results")
        await collection.insert_one(comparison_data)
    
    @classmethod
    async def get_comparison_results(cls, session_id: str) -> Optional[Dict]:
        """Get comparison results"""
        collection = cls.get_collection("comparison_results")
        return await collection.find_one({"session_id": session_id})
    
    # ===== MODIFICATION LOGS =====
    
    @classmethod
    async def log_modification(cls, log_data: Dict):
        """Log a modification request"""
        collection = cls.get_collection("modification_logs")
        await collection.insert_one(log_data)

# Create global instance
db = MongoDB()