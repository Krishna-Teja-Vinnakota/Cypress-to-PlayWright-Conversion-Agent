# backend/services/gemini_converter.py
# Gemini AI integration for converting Cypress to Playwright

import vertexai
from vertexai.generative_models import GenerativeModel, Part
from backend.config import settings
from backend.utils.prompts import build_conversion_prompt
from typing import Optional
import asyncio

class GeminiConverter:
    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.VERTEX_AI_LOCATION
        )
        self.model = GenerativeModel(settings.GEMINI_MODEL)
    
    async def convert_cypress_to_playwright(
        self,
        filename: str,
        file_type: str,
        cypress_code: str
    ) -> Optional[str]:
        """
        Convert Cypress code to Playwright using Gemini
        
        Args:
            filename: Original filename (e.g., "login.cy.js")
            file_type: "js" or "ts"
            cypress_code: The Cypress test code
            
        Returns:
            Converted Playwright code or None if failed
        """
        try:
            # Build prompt
            system_prompt, user_prompt = build_conversion_prompt(
                filename=filename,
                file_type=file_type,
                cypress_code=cypress_code
            )
            
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Call Gemini API (async)
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config={
                    "temperature": 0.2,  # Low temperature for consistent output
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 26000,
                }
            )
            
            # Extract code
            playwright_code = response.text.strip()
            
            # Clean up - remove markdown if present
            playwright_code = self._clean_code_output(playwright_code)
            
            return playwright_code
            
        except Exception as e:
            print(f"❌ Gemini conversion error: {str(e)}")
            return None
    
    def _clean_code_output(self, code: str) -> str:
        """Remove markdown code blocks if present"""
        # Remove ```javascript or ```typescript or ```
        if code.startswith("```"):
            lines = code.split("\n")
            # Remove first line (```language)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        
        return code.strip()

# Global instance
gemini_converter = GeminiConverter()