# backend/services/gemini_modifier.py
# Gemini AI integration for modifying/fixing Playwright code

import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image
from backend.config import settings
from backend.utils.prompts import build_modification_prompt
from typing import Optional
import asyncio
import base64
from PIL import Image as PILImage
import io

class GeminiModifier:
    def __init__(self):
        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.VERTEX_AI_LOCATION
        )
        self.model = GenerativeModel(settings.GEMINI_MODEL)
    
    async def fix_playwright_code(
        self,
        user_query: str,
        cypress_code: str,
        playwright_code: str,
        error_message: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Fix Playwright code based on user feedback
        
        Args:
            user_query: User's description of the issue
            cypress_code: Original Cypress code for reference
            playwright_code: Current Playwright code with issues
            error_message: Optional error message
            image_path: Optional path to screenshot of error
            
        Returns:
            Fixed Playwright code or None if failed
        """
        try:
            # Build text prompts
            system_prompt, user_prompt = build_modification_prompt(
                user_query=user_query,
                error_message=error_message,
                cypress_code=cypress_code,
                playwright_code=playwright_code
            )
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Prepare content parts
            content_parts = [full_prompt]
            
            # If image provided, add it to the prompt
            if image_path:
                try:
                    image_part = await self._load_image(image_path)
                    if image_part:
                        # Add image context
                        content_parts.insert(0, "Error Screenshot:")
                        content_parts.insert(1, image_part)
                        content_parts.insert(2, "\nBased on the error shown in the screenshot above:")
                except Exception as e:
                    print(f"⚠️ Could not load image: {str(e)}")
            
            # Call Gemini API
            response = await asyncio.to_thread(
                self.model.generate_content,
                content_parts,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 20000,
                }
            )
            
            # Extract fixed code
            fixed_code = response.text.strip()
            fixed_code = self._clean_code_output(fixed_code)
            
            return fixed_code
            
        except Exception as e:
            print(f"❌ Gemini modification error: {str(e)}")
            return None
    
    async def _load_image(self, image_path: str) -> Optional[Part]:
        """Load and prepare image for Gemini Vision API"""
        try:
            # Open and convert image
            with PILImage.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (max 4MB for Vertex AI)
                max_size = (1024, 1024)
                img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
                
                # Convert to bytes
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                image_bytes = buffer.getvalue()
                
                # Create Part for Gemini
                return Part.from_data(data=image_bytes, mime_type="image/jpeg")
                
        except Exception as e:
            print(f"❌ Image loading error: {str(e)}")
            return None
    
    def _clean_code_output(self, code: str) -> str:
        """Remove markdown code blocks if present"""
        if code.startswith("```"):
            lines = code.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        return code.strip()

# Global instance
gemini_modifier = GeminiModifier()