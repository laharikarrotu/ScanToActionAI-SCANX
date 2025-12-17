"""
Prescription Extractor - Extracts medication info from prescription images
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from openai import OpenAI
import base64
import os
import re

class PrescriptionInfo(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    quantity: Optional[str] = None
    refills: Optional[str] = None
    instructions: Optional[str] = None
    prescriber: Optional[str] = None
    date: Optional[str] = None

class PrescriptionExtractor:
    """
    Extracts structured medication information from prescription images
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
    
    def extract_from_image(self, image_data: bytes) -> PrescriptionInfo:
        """
        Extract medication information from prescription image
        """
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        prompt = """Analyze this prescription image and extract all medication information.

Return a JSON object with this structure:
{
  "medication_name": "generic or brand name of the medication",
  "dosage": "e.g., 500mg, 10mg/5ml",
  "frequency": "e.g., twice daily, every 8 hours, as needed",
  "quantity": "number of pills/units",
  "refills": "number of refills allowed",
  "instructions": "full instructions for taking the medication",
  "prescriber": "doctor/pharmacist name if visible",
  "date": "prescription date if visible"
}

Focus on:
- Medication name (both brand and generic if visible)
- Dosage strength
- How often to take it
- Total quantity
- Number of refills
- Special instructions
- Prescriber information
- Date

Be accurate - this information is critical for patient safety."""

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
            
            return PrescriptionInfo(**result_dict)
            
        except Exception as e:
            # Return minimal info on error
            return PrescriptionInfo(
                medication_name="Unknown",
                instructions=f"Error extracting prescription: {str(e)}"
            )
    
    def parse_medication_list(self, text: str) -> List[PrescriptionInfo]:
        """
        Parse a list of medications from text (for multi-prescription scenarios)
        """
        medications = []
        # Simple parsing - can be enhanced
        lines = text.split('\n')
        current_med = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to identify medication name
            if any(keyword in line.lower() for keyword in ['mg', 'ml', 'tablet', 'capsule', 'pill']):
                if current_med:
                    medications.append(PrescriptionInfo(**current_med))
                current_med = {"medication_name": line}
            elif 'dosage' in line.lower() or 'mg' in line.lower():
                current_med['dosage'] = line
            elif any(word in line.lower() for word in ['daily', 'twice', 'every', 'times']):
                current_med['frequency'] = line
        
        if current_med:
            medications.append(PrescriptionInfo(**current_med))
        
        return medications

