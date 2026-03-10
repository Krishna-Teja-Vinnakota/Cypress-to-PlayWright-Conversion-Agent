# backend/services/environment_manager.py
# Manages test environments - copies templates and sets up folders

import os
import shutil
import uuid
import json
from typing import List, Dict
from datetime import datetime
from backend.config import settings

class EnvironmentManager:
    
    @staticmethod
    def create_session_environment(session_id: str) -> str:
        """
        Create session directory - NO COPYING, work directly with templates
        
        Returns: session directory path (just for tracking)
        """
        session_dir = os.path.join(settings.SESSIONS_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create session info file to track which files belong to this session
        session_info = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "files": []
        }
        
        with open(os.path.join(session_dir, "session_info.json"), 'w') as f:
            json.dump(session_info, f)
        
        print(f"✅ Created session tracking: {session_id}")
        return session_dir
    
    @staticmethod
    def save_cypress_file(
        session_dir: str,
        filename: str,
        content: str,
        file_type: str,
        session_id: str
    ) -> str:
        """
        Save Cypress test file directly to template directory with session prefix
        
        Args:
            session_dir: Session directory path (for tracking only)
            filename: Original filename (e.g., "login.cy.js")
            content: File content
            file_type: "js" or "ts"
            session_id: Session ID for unique naming
            
        Returns: Full path to saved file
        """
        # Determine target directory - DIRECTLY in templates!
        if file_type == "js":
            target_dir = os.path.join(settings.TEMPLATES_DIR, "cypress-js", "cypress", "e2e")
        else:  # ts
            target_dir = os.path.join(settings.TEMPLATES_DIR, "cypress-ts", "cypress", "e2e")
        
        os.makedirs(target_dir, exist_ok=True)
        
        # Add session prefix to avoid conflicts
        session_filename = f"{session_id}_{filename}"
        file_path = os.path.join(target_dir, session_filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Saved Cypress file directly to template: {file_path}")
        return file_path
    
    @staticmethod
    def save_playwright_file(
        session_dir: str,
        filename: str,
        content: str,
        file_type: str,
        session_id: str
    ) -> str:
        """
        Save Playwright test file directly to template directory with session prefix
        
        Args:
            session_dir: Session directory path (for tracking only)
            filename: Converted filename (e.g., "login.spec.js")
            content: File content
            file_type: "js" or "ts"
            session_id: Session ID for unique naming
            
        Returns: Full path to saved file
        """
        # Determine target directory - DIRECTLY in templates!
        if file_type == "js":
            target_dir = os.path.join(settings.TEMPLATES_DIR, "playwright-js", "tests")
        else:  # ts
            target_dir = os.path.join(settings.TEMPLATES_DIR, "playwright-ts", "tests")
        
        os.makedirs(target_dir, exist_ok=True)
        
        # Add session prefix to avoid conflicts
        session_filename = f"{session_id}_{filename}"
        file_path = os.path.join(target_dir, session_filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Saved Playwright file directly to template: {file_path}")
        return file_path
    
    @staticmethod
    def convert_filename(cypress_filename: str) -> str:
        """
        Convert Cypress filename to Playwright filename
        login.cy.js -> login.spec.js
        dashboard.cy.ts -> dashboard.spec.ts
        """
        if ".cy.js" in cypress_filename:
            return cypress_filename.replace(".cy.js", ".spec.js")
        elif ".cy.ts" in cypress_filename:
            return cypress_filename.replace(".cy.ts", ".spec.ts")
        return cypress_filename
    
    @staticmethod
    def cleanup_session(session_id: str):
        """Remove only test files with session prefix from templates"""
        # Clean up Cypress files
        cypress_js_dir = os.path.join(settings.TEMPLATES_DIR, "cypress-js", "cypress", "e2e")
        cypress_ts_dir = os.path.join(settings.TEMPLATES_DIR, "cypress-ts", "cypress", "e2e")
        
        # Clean up Playwright files
        playwright_js_dir = os.path.join(settings.TEMPLATES_DIR, "playwright-js", "tests")
        playwright_ts_dir = os.path.join(settings.TEMPLATES_DIR, "playwright-ts", "tests")
        
        directories = [cypress_js_dir, cypress_ts_dir, playwright_js_dir, playwright_ts_dir]
        
        for directory in directories:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.startswith(f"{session_id}_"):
                        file_path = os.path.join(directory, filename)
                        os.remove(file_path)
                        print(f"🗑️ Cleaned up: {filename}")
        
        # Remove session tracking directory
        session_dir = os.path.join(settings.SESSIONS_DIR, session_id)
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
            
        print(f"🗑️ Cleaned up session: {session_id}")

environment_manager = EnvironmentManager()