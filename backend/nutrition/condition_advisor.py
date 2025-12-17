"""
Condition-Based Dietary Advisor
Provides personalized nutrition recommendations based on medical diagnoses
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DietaryRecommendation(BaseModel):
    condition: str
    foods_to_eat: List[str]
    foods_to_avoid: List[str]
    key_nutrients: List[str]
    daily_goals: Dict[str, Any]
    sample_meals: List[str]
    important_notes: List[str]

class ConditionAdvisor:
    """
    Provides dietary recommendations based on medical conditions
    """
    
    def __init__(self):
        self.condition_guidelines = self._load_condition_guidelines()
    
    def _load_condition_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """
        Load dietary guidelines for common medical conditions
        In production, this would come from a medical nutrition therapy database
        """
        return {
            "diabetes": {
                "foods_to_eat": [
                    "Non-starchy vegetables (broccoli, spinach, bell peppers)",
                    "Whole grains (quinoa, brown rice, oats)",
                    "Lean proteins (chicken, fish, tofu)",
                    "Healthy fats (avocado, nuts, olive oil)",
                    "Berries and low-sugar fruits"
                ],
                "foods_to_avoid": [
                    "Sugary drinks and sodas",
                    "White bread and refined grains",
                    "Processed snacks",
                    "High-sugar fruits (mangoes, bananas in excess)",
                    "Fried foods"
                ],
                "key_nutrients": ["Fiber", "Complex carbohydrates", "Protein", "Healthy fats"],
                "daily_goals": {
                    "carbs": "45-60g per meal",
                    "fiber": "25-30g",
                    "protein": "15-20% of calories"
                },
                "sample_meals": [
                    "Grilled salmon with quinoa and steamed broccoli",
                    "Greek yogurt with berries and nuts",
                    "Chicken salad with mixed greens and olive oil dressing"
                ],
                "important_notes": [
                    "Monitor blood sugar levels",
                    "Eat at regular intervals",
                    "Choose low glycemic index foods",
                    "Stay hydrated with water"
                ]
            },
            "hypertension": {
                "foods_to_eat": [
                    "Fresh fruits and vegetables",
                    "Whole grains",
                    "Low-fat dairy",
                    "Lean proteins",
                    "Nuts and seeds",
                    "Foods rich in potassium (bananas, sweet potatoes)"
                ],
                "foods_to_avoid": [
                    "High-sodium foods (processed meats, canned foods)",
                    "Salty snacks",
                    "Fast food",
                    "Excessive alcohol",
                    "High-sodium condiments"
                ],
                "key_nutrients": ["Potassium", "Magnesium", "Calcium", "Low sodium"],
                "daily_goals": {
                    "sodium": "Less than 2,300mg (ideally 1,500mg)",
                    "potassium": "4,700mg",
                    "calcium": "1,000-1,200mg"
                },
                "sample_meals": [
                    "Baked chicken with sweet potato and green beans",
                    "Oatmeal with banana and almonds",
                    "Salmon with brown rice and steamed vegetables"
                ],
                "important_notes": [
                    "Follow DASH diet principles",
                    "Read food labels for sodium content",
                    "Cook at home to control salt",
                    "Limit processed foods"
                ]
            },
            "heart_disease": {
                "foods_to_eat": [
                    "Fatty fish (salmon, mackerel, sardines)",
                    "Nuts and seeds",
                    "Olive oil",
                    "Whole grains",
                    "Fruits and vegetables",
                    "Legumes"
                ],
                "foods_to_avoid": [
                    "Trans fats",
                    "Saturated fats (red meat, butter)",
                    "Processed meats",
                    "High-sodium foods",
                    "Sugary foods and drinks"
                ],
                "key_nutrients": ["Omega-3 fatty acids", "Fiber", "Antioxidants", "Low saturated fat"],
                "daily_goals": {
                    "saturated_fat": "Less than 7% of calories",
                    "cholesterol": "Less than 200mg",
                    "fiber": "25-30g"
                },
                "sample_meals": [
                    "Grilled salmon with quinoa and roasted vegetables",
                    "Mediterranean salad with olive oil",
                    "Oatmeal with walnuts and berries"
                ],
                "important_notes": [
                    "Focus on Mediterranean diet principles",
                    "Include omega-3 rich foods",
                    "Limit red meat",
                    "Choose plant-based proteins"
                ]
            },
            "kidney_disease": {
                "foods_to_eat": [
                    "Low-protein options (in moderation)",
                    "Low-phosphorus foods (white bread, rice)",
                    "Low-potassium foods (apples, berries, cabbage)",
                    "Healthy fats in moderation"
                ],
                "foods_to_avoid": [
                    "High-protein foods (excess)",
                    "High-phosphorus foods (dairy, nuts, beans)",
                    "High-potassium foods (bananas, oranges, potatoes)",
                    "Processed foods with additives"
                ],
                "key_nutrients": ["Controlled protein", "Low phosphorus", "Low potassium", "Controlled sodium"],
                "daily_goals": {
                    "protein": "0.6-0.8g per kg body weight",
                    "phosphorus": "800-1,000mg",
                    "potassium": "2,000-3,000mg (varies by stage)"
                },
                "sample_meals": [
                    "White rice with steamed vegetables",
                    "Apple with low-phosphorus bread",
                    "Chicken breast (small portion) with rice"
                ],
                "important_notes": [
                    "Consult with renal dietitian",
                    "Monitor lab values regularly",
                    "Limit fluid intake if needed",
                    "Avoid high-sodium foods"
                ]
            },
            "ibs": {
                "foods_to_eat": [
                    "Low-FODMAP vegetables (carrots, zucchini, spinach)",
                    "Low-FODMAP fruits (strawberries, blueberries, oranges)",
                    "Gluten-free grains (rice, quinoa)",
                    "Lean proteins",
                    "Lactose-free dairy"
                ],
                "foods_to_avoid": [
                    "High-FODMAP foods (onions, garlic, wheat)",
                    "Dairy (if lactose intolerant)",
                    "Beans and legumes",
                    "Certain fruits (apples, pears, mangoes)",
                    "Artificial sweeteners"
                ],
                "key_nutrients": ["Low-FODMAP foods", "Fiber (soluble)", "Probiotics", "Hydration"],
                "daily_goals": {
                    "fiber": "Gradually increase soluble fiber",
                    "water": "8-10 glasses",
                    "small_meals": "Eat smaller, frequent meals"
                },
                "sample_meals": [
                    "Grilled chicken with rice and carrots",
                    "Lactose-free yogurt with strawberries",
                    "Salmon with quinoa and spinach"
                ],
                "important_notes": [
                    "Follow low-FODMAP diet initially",
                    "Keep a food diary",
                    "Identify trigger foods",
                    "Eat slowly and chew thoroughly"
                ]
            }
        }
    
    def get_recommendations(self, condition: str) -> Optional[DietaryRecommendation]:
        """
        Get dietary recommendations for a specific condition
        """
        condition_lower = condition.lower()
        
        # Try to match condition
        for key, guidelines in self.condition_guidelines.items():
            if key in condition_lower or condition_lower in key:
                return DietaryRecommendation(
                    condition=key,
                    **guidelines
                )
        
        # If no exact match, return general healthy eating guidelines
        return DietaryRecommendation(
            condition=condition,
            foods_to_eat=[
                "Fresh fruits and vegetables",
                "Whole grains",
                "Lean proteins",
                "Healthy fats",
                "Plenty of water"
            ],
            foods_to_avoid=[
                "Processed foods",
                "Excessive sugar",
                "Trans fats",
                "High-sodium foods"
            ],
            key_nutrients=["Fiber", "Protein", "Vitamins", "Minerals"],
            daily_goals={"water": "8-10 glasses", "fruits_vegetables": "5-7 servings"},
            sample_meals=[
                "Balanced meal with protein, vegetables, and whole grains",
                "Fresh fruit and nuts as snacks",
                "Colorful salad with lean protein"
            ],
            important_notes=[
                "Consult with healthcare provider for specific dietary needs",
                "Eat a variety of foods",
                "Stay hydrated",
                "Listen to your body"
            ]
        )
    
    def check_food_compatibility(self, food_name: str, condition: str) -> Dict[str, Any]:
        """
        Check if a specific food is compatible with a condition
        """
        recommendation = self.get_recommendations(condition)
        if not recommendation:
            return {"compatible": True, "reason": "No specific restrictions found"}
        
        food_lower = food_name.lower()
        
        # Check foods to avoid
        for avoid_food in recommendation.foods_to_avoid:
            if avoid_food.lower() in food_lower or food_lower in avoid_food.lower():
                return {
                    "compatible": False,
                    "reason": f"This food is not recommended for {condition}",
                    "severity": "moderate"
                }
        
        # Check foods to eat
        for eat_food in recommendation.foods_to_eat:
            if eat_food.lower() in food_lower or food_lower in eat_food.lower():
                return {
                    "compatible": True,
                    "reason": f"This food is recommended for {condition}",
                    "severity": "good"
                }
        
        return {
            "compatible": True,
            "reason": "Food compatibility unclear - consult with healthcare provider",
            "severity": "neutral"
        }

