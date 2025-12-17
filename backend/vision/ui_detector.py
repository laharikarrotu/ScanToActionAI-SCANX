"""
Vision Engine - Uses multimodal LLM to understand UI from images
"""
import base64
from typing import Optional, Dict, Any
from openai import OpenAI
from pydantic import BaseModel
import os

class UIElement(BaseModel):
    id: str
    type: str  # button, input, text, link, etc.
    label: str
    value: Optional[str] = None
    position: Optional[Dict[str, int]] = None

class UISchema(BaseModel):
    page_type: str
    url_hint: Optional[str] = None
    elements: list[UIElement]

class VisionEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # or "gpt-4-turbo" for vision
    
    def analyze_image(self, image_data: bytes, hint: Optional[str] = None) -> UISchema:
        """
        Takes image bytes and returns structured UI schema
        """
        # Convert image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Build prompt
        prompt = """Analyze this healthcare-related interface (medical form, prescription, insurance card, appointment booking, etc.) and extract all interactive and important elements.
        
This could be a medical form, prescription label, insurance card, appointment booking page, patient portal, or other healthcare document.
        
Return a JSON object with this structure:
{
  "page_type": "booking_page" | "form" | "product_page" | "dashboard" | "other",
  "url_hint": "guessed URL if visible",
  "elements": [
    {
      "id": "unique_id_like_btn_book",
      "type": "button" | "input" | "text" | "link" | "select" | "checkbox" | "radio",
      "label": "visible text or label",
      "value": "current value if input/select",
      "position": {"x": 100, "y": 200} // optional, approximate
    }
  ]
}

Focus on:
- Medical form fields (patient name, DOB, SSN, insurance info, medical history, symptoms)
- Prescription information (medication name, dosage, instructions, refills)
- Insurance card details (member ID, group number, policy holder)
- Appointment booking elements (date pickers, time slots, provider selection)
- Buttons and clickable elements
- Input fields and their labels
- Important healthcare information (dates, names, medical terms, dosages)
- Navigation elements

Be thorough - include all actionable elements."""
        
        if hint:
            prompt += f"\n\nContext hint: {hint}"
        
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
            # Parse JSON response
            import json
            result_dict = json.loads(result_text)
            
            # Convert to UISchema
            elements = [UIElement(**elem) for elem in result_dict.get("elements", [])]
            
            return UISchema(
                page_type=result_dict.get("page_type", "unknown"),
                url_hint=result_dict.get("url_hint"),
                elements=elements
            )
            
        except Exception as e:
            # Fallback schema on error
            return UISchema(
                page_type="error",
                elements=[],
                url_hint=None
            )

