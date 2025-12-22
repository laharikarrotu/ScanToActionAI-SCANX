"""
Food Scanner - Extracts nutritional information from food labels
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel
import base64
import os
import json
import re

# Try Gemini first, fallback to OpenAI
try:
    import google.generativeai as genai
    from PIL import Image
    import io
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    Image = None
    io = None

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

class NutritionFacts(BaseModel):
    serving_size: Optional[str] = None
    calories: Optional[int] = None
    total_fat: Optional[str] = None
    saturated_fat: Optional[str] = None
    trans_fat: Optional[str] = None
    cholesterol: Optional[str] = None
    sodium: Optional[str] = None
    total_carbs: Optional[str] = None
    dietary_fiber: Optional[str] = None
    sugars: Optional[str] = None
    protein: Optional[str] = None
    vitamins: Optional[Dict[str, str]] = None
    ingredients: Optional[str] = None

class FoodScanner:
    """
    Extracts nutritional information from food label images
    """
    
    def __init__(self, api_key: Optional[str] = None, use_gemini: bool = True):
        # FORCE GEMINI ONLY - OpenAI removed
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required. OpenAI has been removed.")
        
        self.use_gemini = True
        genai.configure(api_key=self.gemini_api_key)
        from core.gemini_helper import get_gemini_model_with_fallback
        self.model = get_gemini_model_with_fallback(api_key=self.gemini_api_key)
        self.client = None
        self.model_name = None
        self.openai_api_key = None
    
    def extract_nutrition_facts(self, image_data: bytes) -> NutritionFacts:
        """
        Extract nutrition facts from food label image
        """
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        prompt = """Analyze this food label/nutrition facts panel and extract all nutritional information.

Return a JSON object with this structure:
{
  "serving_size": "e.g., 1 cup (240ml)",
  "calories": 250,
  "total_fat": "10g",
  "saturated_fat": "2g",
  "trans_fat": "0g",
  "cholesterol": "5mg",
  "sodium": "300mg",
  "total_carbs": "30g",
  "dietary_fiber": "3g",
  "sugars": "8g",
  "protein": "5g",
  "vitamins": {
    "Vitamin A": "10%",
    "Vitamin C": "5%"
  },
  "ingredients": "Full ingredients list if visible"
}

Extract all visible nutrition information. If a value is not visible, set it to null."""

        try:
            if self.use_gemini and self.model:
                # Use Gemini
                image = Image.open(io.BytesIO(image_data))
                full_prompt = f"""{prompt}

Return ONLY valid JSON, no other text."""
                response = self.model.generate_content(
                    [full_prompt, image],
                    generation_config={
                        "temperature": 0.1,
                        "max_output_tokens": 2000,
                    }
                )
                result_text = response.text
                # Try to extract JSON if wrapped in markdown
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(1)
                result_dict = json.loads(result_text)
            else:
                raise ValueError("Gemini model not initialized. GEMINI_API_KEY is required.")
            
            # Handle vitamins separately
            vitamins = result_dict.pop("vitamins", None)
            
            return NutritionFacts(
                **result_dict,
                vitamins=vitamins
            )
            
        except Exception as e:
            return NutritionFacts(
                serving_size="Error extracting nutrition facts",
                ingredients=f"Error: {str(e)}"
            )

