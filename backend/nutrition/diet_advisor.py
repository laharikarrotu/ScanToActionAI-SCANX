"""
Diet Advisor - Provides diet recommendations based on medical conditions
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
import json

# Try Gemini first, fallback to OpenAI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

class DietRecommendation(BaseModel):
    condition: str
    foods_to_eat: List[str]
    foods_to_avoid: List[str]
    meal_plan_suggestion: str
    nutritional_focus: str
    warnings: List[str] = []

class MedicationFoodInteraction(BaseModel):
    medication: str
    food: str
    interaction_type: str  # "avoid", "limit", "timing"
    description: str
    severity: str  # "major", "moderate", "minor"

class DietAdvisor:
    """
    Provides personalized diet recommendations based on medical conditions
    """
    
    def __init__(self, api_key: Optional[str] = None, use_gemini: bool = True):
        # Prioritize Gemini if available (cheaper and avoids quota issues)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Force Gemini if key is available, otherwise use OpenAI
        if use_gemini and GEMINI_AVAILABLE and self.gemini_api_key:
            self.use_gemini = True
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            self.client = None
        elif OPENAI_AVAILABLE and self.openai_api_key:
            self.use_gemini = False
            self.client = OpenAI(api_key=self.openai_api_key)
            self.model_name = "gpt-4o"
            self.model = None
        else:
            self.use_gemini = False
            self.client = None
            self.model = None
        
        # Common medication-food interactions
        self.medication_food_interactions = {
            "warfarin": {
                "avoid": ["leafy greens (high vitamin K)", "cranberry juice"],
                "limit": ["alcohol"],
                "description": "Vitamin K can interfere with warfarin effectiveness"
            },
            "maoi": {
                "avoid": ["aged cheeses", "fermented foods", "cured meats", "red wine"],
                "description": "Tyramine in these foods can cause dangerous blood pressure spikes"
            },
            "grapefruit": {
                "medications": ["statins", "calcium channel blockers", "some antidepressants"],
                "avoid": ["grapefruit", "grapefruit juice"],
                "description": "Grapefruit can increase medication levels in blood"
            },
            "digoxin": {
                "avoid": ["licorice", "high-fiber foods (timing)"],
                "description": "Can affect absorption"
            }
        }
    
    def get_diet_recommendations(
        self, 
        condition: str,
        medications: Optional[List[str]] = None,
        dietary_restrictions: Optional[List[str]] = None
    ) -> DietRecommendation:
        """
        Get diet recommendations for a specific medical condition
        """
        prompt = f"""Provide diet and nutrition recommendations for someone with: {condition}

Consider:
- Foods that help manage/improve this condition
- Foods to avoid that might worsen symptoms
- Nutritional focus (e.g., low sodium, high fiber, anti-inflammatory)
- Sample meal plan approach

Return a JSON object:
{{
  "condition": "{condition}",
  "foods_to_eat": ["list of recommended foods"],
  "foods_to_avoid": ["list of foods to avoid"],
  "meal_plan_suggestion": "brief description of meal planning approach",
  "nutritional_focus": "main nutritional goals (e.g., 'Low sodium, high potassium, heart-healthy fats')",
  "warnings": ["any important warnings about diet and this condition"]
}}

Be specific and practical. Focus on evidence-based recommendations."""

        if medications:
            prompt += f"\n\nCurrent medications: {', '.join(medications)}"
        
        if dietary_restrictions:
            prompt += f"\n\nDietary restrictions: {', '.join(dietary_restrictions)}"

        try:
            # Try Gemini first (preferred - cheaper and available)
            if self.use_gemini and self.model:
                # Use Gemini
                full_prompt = f"""You are a medical nutritionist. Provide evidence-based dietary advice.

{prompt}

Return ONLY valid JSON, no other text."""
                response = self.model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 2000,
                        "response_mime_type": "application/json"  # Force JSON output
                    }
                )
                result_text = response.text
                # Try to extract JSON if wrapped in markdown
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(1)
                result_dict = json.loads(result_text)
            elif self.client:
                # Use OpenAI (fallback only)
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": "You are a medical nutritionist. Provide evidence-based dietary advice."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.3
                    )
                    result_text = response.choices[0].message.content
                    result_dict = json.loads(result_text)
                except Exception as openai_error:
                    # If OpenAI fails (quota, etc.), try to use Gemini if available
                    error_str = str(openai_error).lower()
                    if ("quota" in error_str or "429" in error_str or "insufficient" in error_str) and self.gemini_api_key:
                        # Retry with Gemini
                        import logging
                        logging.warning(f"OpenAI quota exceeded, switching to Gemini: {openai_error}")
                        # Re-initialize Gemini if not already done
                        if not self.model and GEMINI_AVAILABLE:
                            genai.configure(api_key=self.gemini_api_key)
                            self.model = genai.GenerativeModel('gemini-1.5-pro')
                        if self.model:
                            full_prompt = f"""You are a medical nutritionist. Provide evidence-based dietary advice.

{prompt}

Return ONLY valid JSON, no other text."""
                            response = self.model.generate_content(
                                full_prompt,
                                generation_config={
                                    "temperature": 0.3,
                                    "max_output_tokens": 2000,
                                    "response_mime_type": "application/json"
                                }
                            )
                            result_text = response.text
                            import re
                            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                            if json_match:
                                result_text = json_match.group(1)
                            result_dict = json.loads(result_text)
                        else:
                            raise openai_error
                    else:
                        raise openai_error
            else:
                raise ValueError("No API client available")
            
            # Check for medication-food interactions
            warnings = result_dict.get("warnings", [])
            if medications:
                for med in medications:
                    med_lower = med.lower()
                    interactions = self._check_medication_food_interactions(med_lower)
                    for interaction in interactions:
                        warnings.append(interaction)
            
            result_dict["warnings"] = warnings
            
            return DietRecommendation(**result_dict)
            
        except Exception as e:
            # Fallback recommendations
            return DietRecommendation(
                condition=condition,
                foods_to_eat=["Consult with a registered dietitian"],
                foods_to_avoid=["Consult with a registered dietitian"],
                meal_plan_suggestion="Please consult with a healthcare provider for personalized meal planning",
                nutritional_focus="Personalized nutrition plan needed",
                warnings=[f"Error generating recommendations: {str(e)}"]
            )
    
    def _check_medication_food_interactions(self, medication: str) -> List[str]:
        """Check for known medication-food interactions"""
        warnings = []
        
        # Check direct matches
        if medication in self.medication_food_interactions:
            interaction = self.medication_food_interactions[medication]
            if "avoid" in interaction:
                foods = ", ".join(interaction["avoid"])
                warnings.append(f"⚠️ {medication.title()}: Avoid {foods}. {interaction.get('description', '')}")
        
        # Check for grapefruit interactions
        if "grapefruit" in medication or any(med in medication for med in ["atorvastatin", "simvastatin", "felodipine"]):
            warnings.append("⚠️ Avoid grapefruit and grapefruit juice - can increase medication levels")
        
        return warnings
    
    def check_food_compatibility(
        self,
        food_item: str,
        condition: Optional[str] = None,
        medications: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Check if a specific food is compatible with user's condition/medications
        """
        compatibility = {
            "food": food_item,
            "safe": True,
            "warnings": [],
            "recommendations": []
        }
        
        # Check medication interactions
        if medications:
            for med in medications:
                med_lower = med.lower()
                if med_lower in self.medication_food_interactions:
                    interaction = self.medication_food_interactions[med_lower]
                    if "avoid" in interaction:
                        for avoid_food in interaction["avoid"]:
                            if avoid_food.lower() in food_item.lower() or food_item.lower() in avoid_food.lower():
                                compatibility["safe"] = False
                                compatibility["warnings"].append(
                                    f"{med} interaction: {interaction.get('description', 'May interact with medication')}"
                                )
        
        # Check condition-specific concerns
        if condition:
            condition_lower = condition.lower()
            if "diabetes" in condition_lower:
                high_sugar_foods = ["sugar", "candy", "soda", "juice", "dessert"]
                if any(food in food_item.lower() for food in high_sugar_foods):
                    compatibility["recommendations"].append("Monitor blood sugar - high sugar content")
            
            if "hypertension" in condition_lower or "high blood pressure" in condition_lower:
                high_sodium_foods = ["salt", "sodium", "processed", "canned"]
                if any(food in food_item.lower() for food in high_sodium_foods):
                    compatibility["recommendations"].append("High sodium - limit intake if managing blood pressure")
        
        return compatibility
    
    def generate_meal_plan(
        self,
        condition: str,
        days: int = 7,
        dietary_restrictions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a weekly meal plan for a specific condition
        """
        prompt = f"""Create a {days}-day meal plan for someone with {condition}.

Include:
- Breakfast, lunch, dinner, and 2 snacks per day
- Specific food items and portions
- Nutritional notes for each meal
- Shopping list

Return JSON:
{{
  "condition": "{condition}",
  "days": {days},
  "meal_plan": [
    {{
      "day": 1,
      "breakfast": {{"meal": "...", "nutrition_notes": "..."}},
      "lunch": {{"meal": "...", "nutrition_notes": "..."}},
      "dinner": {{"meal": "...", "nutrition_notes": "..."}},
      "snacks": ["...", "..."]
    }}
  ],
  "shopping_list": ["list of ingredients"],
  "nutritional_goals": "overall goals for this meal plan"
}}"""

        if dietary_restrictions:
            prompt += f"\n\nDietary restrictions: {', '.join(dietary_restrictions)}"

        try:
            if self.use_gemini and self.model:
                # Use Gemini
                full_prompt = f"""You are a registered dietitian creating personalized meal plans.

{prompt}

Return ONLY valid JSON, no other text."""
                response = self.model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": 0.4,
                        "max_output_tokens": 4000,
                    }
                )
                result_text = response.text
                # Try to extract JSON if wrapped in markdown
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(1)
                return json.loads(result_text)
            elif self.client:
                # Use OpenAI
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a registered dietitian creating personalized meal plans."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.4
                )
                result_text = response.choices[0].message.content
                return json.loads(result_text)
            else:
                raise ValueError("No API client available")
            
        except Exception as e:
            return {
                "error": str(e),
                "message": "Please consult with a registered dietitian for a personalized meal plan"
            }

