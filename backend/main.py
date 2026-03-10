# backend/main.py
# Main FastAPI application with all endpoints

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
import uuid
import os
import json
import zipfile
import io
import asyncio
from pathlib import Path
from datetime import datetime
from bson import ObjectId

# Helper function to serialize datetime and ObjectId objects
def serialize_datetime(obj):
    """Convert datetime and ObjectId objects to JSON-serializable formats"""
    if isinstance(obj, dict):
        return {key: serialize_datetime(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

from backend.config import settings
from backend.database.mongodb import db
from backend.services.environment_manager import environment_manager
from backend.services.gemini_converter import gemini_converter
from backend.services.gemini_modifier import gemini_modifier
from backend.services.test_executor import test_executor
from backend.services.comparison import comparison_service

# Ensure directories exist
settings.ensure_directories()

app = FastAPI(
    title="Cypress to Playwright Converter",
    description="AI-powered test conversion tool",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"✅ WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"❌ WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                # Serialize datetime objects before sending
                serialized_message = serialize_datetime(message)
                await self.active_connections[session_id].send_json(serialized_message)
            except Exception as e:
                print(f"Error sending message: {e}")

manager = ConnectionManager()

# ========================================
# STARTUP & SHUTDOWN
# ========================================

@app.on_event("startup")
async def startup_event():
    """Initialize database connection"""
    await db.connect()
    print("🚀 Application started")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection"""
    await db.disconnect()
    print("🛑 Application shutdown")

# ========================================
# BASIC ROUTES
# ========================================

@app.get("/")
async def root():
    """Serve main HTML page"""
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
    return FileResponse(html_path)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ========================================
# SESSION MANAGEMENT
# ========================================

@app.get("/api/last-session")
async def get_last_session():
    """Get the last session if exists"""
    session = await db.get_last_session()
    
    if session:
        return {
            "exists": True,
            "session_id": session["session_id"],
            "created_at": session["created_at"].isoformat(),
            "status": session["status"],
            "files_count": len(session.get("files", []))
        }
    else:
        return {"exists": False}

@app.get("/api/session/{session_id}")
async def get_session_details(session_id: str):
    """Get complete session details"""
    session = await db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Convert datetime objects to ISO strings
    session["created_at"] = session["created_at"].isoformat()
    session["last_accessed"] = session["last_accessed"].isoformat()
    
    # Clean up MongoDB _id
    session.pop("_id", None)
    
    return session

# ========================================
# FILE UPLOAD
# ========================================

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload Cypress test files
    
    1. Generate session ID
    2. Create session environment
    3. Save files to appropriate locations
    4. Store metadata in MongoDB
    """
    try:
        # Generate unique session ID
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        # Create session directory and copy templates
        session_dir = environment_manager.create_session_environment(session_id)
        
        # Process each file
        file_data = []
        
        for file in files:
            # Validate file extension
            if not (file.filename.endswith(".cy.js") or file.filename.endswith(".cy.ts")):
                continue
            
            # Determine file type
            file_type = "ts" if file.filename.endswith(".cy.ts") else "js"
            
            # Generate file ID
            file_id = f"file_{uuid.uuid4().hex[:8]}"
            
            # Read file content
            content = await file.read()
            cypress_code = content.decode('utf-8')
            
            # Save to appropriate Cypress environment
            cypress_path = environment_manager.save_cypress_file(
                session_dir=session_dir,
                filename=file.filename,
                content=cypress_code,
                file_type=file_type,
                session_id=session_id
            )
            
            # Prepare file data for MongoDB
            file_data.append({
                "file_id": file_id,
                "original_name": file.filename,
                "file_type": file_type,
                "cypress_code": cypress_code,
                "cypress_path": cypress_path,
                "playwright_versions": [],  # Will be populated during conversion
                "current_version": 0,
                "approved_version": None,
                "playwright_path": None
            })
        
        # Create session in MongoDB
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "status": "uploaded",
            "target_url": None,
            "files": file_data
        }
        
        await db.create_session(session_data)
        
        # Trigger automatic conversion in background
        asyncio.create_task(auto_convert_files(session_id))
        
        return {
            "success": True,
            "session_id": session_id,
            "files": [
                {
                    "file_id": f["file_id"],
                    "name": f["original_name"],
                    "type": f["file_type"]
                }
                for f in file_data
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ========================================
# CONVERSION
# ========================================

async def auto_convert_files(session_id: str):
    """Background task to auto-convert files after upload"""
    try:
        await manager.send_message(session_id, {
            "type": "conversion_start",
            "message": "Starting conversion..."
        })
        
        # Update session status
        await db.update_session(session_id, {"status": "converting"})
        
        # Get session data
        session = await db.get_session(session_id)
        if not session:
            return
        
        session_dir = os.path.join(settings.SESSIONS_DIR, session_id)
        total_files = len(session["files"])
        converted_count = 0
        
        # Convert each file
        for file_data in session["files"]:
            # Send progress update
            await manager.send_message(session_id, {
                "type": "conversion_progress",
                "file_id": file_data["file_id"],
                "file_name": file_data["original_name"],
                "progress": int((converted_count / total_files) * 100)
            })
            
            # Call Gemini for conversion
            playwright_code = await gemini_converter.convert_cypress_to_playwright(
                filename=file_data["original_name"],
                file_type=file_data["file_type"],
                cypress_code=file_data["cypress_code"]
            )
            
            if playwright_code:
                # Convert filename
                playwright_filename = environment_manager.convert_filename(
                    file_data["original_name"]
                )
                
                # Save to Playwright environment
                playwright_path = environment_manager.save_playwright_file(
                    session_dir=session_dir,
                    filename=playwright_filename,
                    content=playwright_code,
                    file_type=file_data["file_type"],
                    session_id=session_id
                )
                
                # Create version 1
                version_data = {
                    "version": 1,
                    "code": playwright_code,
                    "created_at": datetime.now(),
                    "source": "gemini_conversion",
                    "modification_request": None
                }
                
                # Add to MongoDB
                await db.add_file_version(
                    session_id=session_id,
                    file_id=file_data["file_id"],
                    version_data=version_data
                )
                
                converted_count += 1
                
                # Send completion for this file
                await manager.send_message(session_id, {
                    "type": "conversion_done",
                    "file_id": file_data["file_id"],
                    "version": 1
                })
        
        # Update session status
        await db.update_session(session_id, {"status": "converted"})
        
        # Send final completion message
        await manager.send_message(session_id, {
            "type": "conversion_complete",
            "total": total_files,
            "converted": converted_count
        })
        
    except Exception as e:
        print(f"❌ Conversion error: {str(e)}")
        await manager.send_message(session_id, {
            "type": "conversion_error",
            "error": str(e)
        })

# ========================================
# WebSocket
# ========================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket connection for real-time updates"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back (optional)
            await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)

# ========================================
# CYPRESS EXECUTION
# ========================================

@app.post("/api/cypress/execute")
async def execute_cypress(
    session_id: str = Form(...),
    target_url: str = Form(...)
):
    """Execute Cypress tests directly from templates"""
    try:
        # Update session with target URL
        await db.update_session(session_id, {
            "target_url": target_url,
            "status": "cypress_running"
        })
        
        # Send status update
        await manager.send_message(session_id, {
            "type": "cypress_running",
            "message": "Executing Cypress tests..."
        })
        
        # Get session
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Group files by type
        js_files = [f for f in session["files"] if f["file_type"] == "js"]
        ts_files = [f for f in session["files"] if f["file_type"] == "ts"]
        
        all_tests = []
        
        # Run JS tests if any
        if js_files:
            results = await test_executor.run_cypress_tests(
                session_id=session_id,
                file_type="js",
                target_url=target_url
            )
            if results.get("success"):
                all_tests.extend(results["tests"])
        
        # Run TS tests if any
        if ts_files:
            results = await test_executor.run_cypress_tests(
                session_id=session_id,
                file_type="ts",
                target_url=target_url
            )
            if results.get("success"):
                all_tests.extend(results["tests"])
        
        # Calculate summary
        total = len(all_tests)
        passed = sum(1 for t in all_tests if t["status"] == "passed")
        
        # Save results to MongoDB
        results_data = {
            "session_id": session_id,
            "executed_at": datetime.now(),
            "target_url": target_url,
            "tests": all_tests,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "duration": sum(t["duration"] for t in all_tests)
            }
        }
        
        await db.save_cypress_results(results_data)
        
        # Update session status
        await db.update_session(session_id, {"status": "cypress_completed"})
        
        # Send completion message
        await manager.send_message(session_id, {
            "type": "cypress_done",
            "results": results_data
        })
        
        return {"success": True, "message": "Cypress tests completed"}
        
    except Exception as e:
        await manager.send_message(session_id, {
            "type": "cypress_error", 
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Cypress execution failed: {str(e)}")

# ========================================
# PLAYWRIGHT EXECUTION
# ========================================

@app.post("/api/playwright/execute")
async def execute_playwright(
    session_id: str = Form(...),
    target_url: str = Form(...)
):
    """Execute Playwright tests directly from templates"""
    try:
        # Update session with target URL
        await db.update_session(session_id, {
            "target_url": target_url,
            "status": "playwright_running"
        })
        
        # Send status update
        await manager.send_message(session_id, {
            "type": "playwright_running",
            "message": "Executing Playwright tests..."
        })
        
        # Get session
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Group files by type
        js_files = [f for f in session["files"] if f["file_type"] == "js"]
        ts_files = [f for f in session["files"] if f["file_type"] == "ts"]
        
        all_tests = []
        
        # Run JS tests if any
        if js_files:
            results = await test_executor.run_playwright_tests(
                session_id=session_id,
                file_type="js",
                target_url=target_url
            )
            if results.get("success"):
                all_tests.extend(results["tests"])
        
        # Run TS tests if any
        if ts_files:
            results = await test_executor.run_playwright_tests(
                session_id=session_id,
                file_type="ts",
                target_url=target_url
            )
            if results.get("success"):
                all_tests.extend(results["tests"])
        
        # Calculate summary
        total = len(all_tests)
        passed = sum(1 for t in all_tests if t["status"] == "passed")
        failed = total - passed
        duration = sum(t["duration"] for t in all_tests)
        
        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "duration": duration
        }
        
        # Send results via WebSocket
        await manager.send_message(session_id, {
            "type": "playwright_done",
            "results": {
                "tests": all_tests,
                "summary": summary
            }
        })
        
        # Update session
        await db.update_session(session_id, {
            "status": "playwright_completed",
            "playwright_results": {
                "tests": all_tests,
                "summary": summary
            }
        })
        
        return {"success": True, "message": "Playwright tests completed"}
        
    except Exception as e:
        await manager.send_message(session_id, {
            "type": "playwright_error", 
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Playwright execution failed: {str(e)}")

# ========================================
# FILE DETAILS & MODIFICATION
# ========================================

@app.get("/api/file/{session_id}/{file_id}")
async def get_file_details(session_id: str, file_id: str):
    """Get file details for review"""
    file_data = await db.get_file_data(session_id, file_id)
    
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Convert datetime objects in versions
    for version in file_data.get("playwright_versions", []):
        if isinstance(version.get("created_at"), datetime):
            version["created_at"] = version["created_at"].isoformat()
    
    return {
        "file_id": file_data["file_id"],
        "file_name": environment_manager.convert_filename(file_data["original_name"]),
        "cypress_code": file_data["cypress_code"],
        "current_version": file_data["current_version"],
        "approved_version": file_data.get("approved_version"),
        "playwright_versions": file_data["playwright_versions"]
    }

@app.post("/api/select-version")
async def select_version(
    session_id: str = Form(...),
    file_id: str = Form(...),
    version: int = Form(...)
):
    """User selects a specific version from sidebar"""
    # Update current_version in MongoDB
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Find file and update
    for i, file_data in enumerate(session["files"]):
        if file_data["file_id"] == file_id:
            await db.update_session(session_id, {
                f"files.{i}.current_version": version
            })
            
            # Get version code
            for v in file_data["playwright_versions"]:
                if v["version"] == version:
                    return {
                        "success": True,
                        "version": version,
                        "code": v["code"]
                    }
    
    raise HTTPException(status_code=404, detail="Version not found")

@app.post("/api/approve")
async def approve_version(
    session_id: str = Form(...),
    file_id: str = Form(...),
    version: int = Form(...)
):
    """User approves a version for execution"""
    await db.set_approved_version(session_id, file_id, version)
    
    return {
        "success": True,
        "approved_version": version
    }

@app.post("/api/modify")
async def modify_code(
    session_id: str = Form(...),
    file_id: str = Form(...),
    query: Optional[str] = Form(None),
    error_text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """Request code modification from Gemini"""
    try:
        # Send processing message
        await manager.send_message(session_id, {
            "type": "modification_processing",
            "file_id": file_id
        })
        
        # Get file data
        file_data = await db.get_file_data(session_id, file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get current version code
        current_version = file_data["current_version"]
        current_code = None
        
        for version in file_data["playwright_versions"]:
            if version["version"] == current_version:
                current_code = version["code"]
                break
        
        if not current_code:
            raise HTTPException(status_code=400, detail="No current version found")
        
        # Handle image upload if provided
        image_path = None
        if image:
            # Save image
            upload_dir = os.path.join(settings.UPLOADS_DIR, session_id)
            os.makedirs(upload_dir, exist_ok=True)
            
            image_path = os.path.join(upload_dir, f"{file_id}_{uuid.uuid4().hex[:8]}.jpg")
            
            with open(image_path, "wb") as f:
                content = await image.read()
                f.write(content)
        
        # Call Gemini for modification
        fixed_code = await gemini_modifier.fix_playwright_code(
            user_query=query or "",
            cypress_code=file_data["cypress_code"],
            playwright_code=current_code,
            error_message=error_text,
            image_path=image_path
        )
        
        if not fixed_code:
            raise HTTPException(status_code=500, detail="Modification failed")
        
        # Create new version
        new_version = current_version + 1
        version_data = {
            "version": new_version,
            "code": fixed_code,
            "created_at": datetime.now(),
            "source": "user_modification",
            "modification_request": {
                "query": query,
                "error_text": error_text,
                "image_path": image_path
            }
        }
        
        # Add to MongoDB
        await db.add_file_version(
            session_id=session_id,
            file_id=file_id,
            version_data=version_data
        )
        
        # Send completion message
        await manager.send_message(session_id, {
            "type": "modification_done",
            "file_id": file_id,
            "version": new_version
        })
        
        return {
            "success": True,
            "new_version": new_version,
            "code": fixed_code
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Modification failed: {str(e)}")

# ========================================
# DOWNLOAD
# ========================================

@app.get("/api/download/{session_id}/{file_id}")
async def download_file(session_id: str, file_id: str):
    """Download the Playwright converted file as .spec.ts"""
    try:
        # Get file details
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Find the file
        file_data = None
        for f in session["files"]:
            if f["file_id"] == file_id:
                file_data = f
                break
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the latest Playwright version
        playwright_versions = file_data.get("playwright_versions", [])
        if not playwright_versions:
            raise HTTPException(status_code=404, detail="No Playwright code available")
        
        latest_version = playwright_versions[-1]
        code = latest_version.get("code", "")
        
        # Create filename - convert .cy.js/.cy.ts to .spec.ts
        original_name = file_data["original_filename"]
        # Remove .cy.js or .cy.ts extension
        base_name = original_name.replace('.cy.js', '').replace('.cy.ts', '')
        download_filename = f"{base_name}.spec.ts"
        
        # Return as downloadable file
        from fastapi.responses import Response
        return Response(
            content=code,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )