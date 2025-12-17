"""
Food Scanner - Extracts nutritional information from food labels
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel
from openai import OpenAI
import base64
import os

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
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
    
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            import json
            result_dict = json.loads(result_text)
            
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

