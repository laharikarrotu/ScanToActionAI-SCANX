"""
Prescription Extractor - Extracts medication info from prescription images
Supports both OpenAI and Gemini (prioritizes Gemini if available)
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import base64
import os
import re
import json

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

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
    Uses Gemini if available (cheaper), otherwise falls back to OpenAI
    """
    
    def __init__(self, api_key: Optional[str] = None, gemini_api_key: Optional[str] = None, use_gemini: bool = True):
        # FORCE GEMINI ONLY - OpenAI removed
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required. OpenAI has been removed.")
        
        genai.configure(api_key=self.gemini_api_key)
        from core.gemini_helper import get_gemini_model_with_fallback
        self.model = get_gemini_model_with_fallback(api_key=self.gemini_api_key)
        self.use_gemini = True
        self.client = None
        self.openai_model = None
    
    def _validate_dosage(self, dosage: Optional[str], medication_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate dosage for safety - check for suspicious values that might indicate OCR errors.
        
        Returns:
            (is_valid, warning_message)
        """
        if not dosage:
            return True, None  # Dosage is optional
        
        dosage_lower = dosage.lower().strip()
        
        # Check for suspicious patterns that might indicate misread numbers
        # Common OCR errors: 5mg -> 50mg, 10mg -> 100mg, etc.
        
        # Extract numeric values from dosage
        numbers = re.findall(r'\d+', dosage)
        if not numbers:
            return True, None  # No numbers found, can't validate
        
        # Check for extremely high values (likely OCR error)
        for num_str in numbers:
            try:
                num = int(num_str)
                # Flag suspiciously high dosages (e.g., > 1000mg for most medications)
                # This is a heuristic - some medications do have high dosages
                if num > 10000:  # Very high, likely error
                    return False, f"WARNING: Dosage value {num} seems unusually high. Please verify the prescription image is clear and the dosage is correct."
                if num > 1000 and 'mg' in dosage_lower:  # High but possible
                    return True, f"CAUTION: Dosage {dosage} is high. Please verify this is correct."
            except ValueError:
                continue
        
        # Check for suspicious patterns (e.g., "50mg" when it should be "5mg")
        # This is a heuristic - we can't be 100% sure, but we can flag potential issues
        suspicious_patterns = [
            (r'(\d)0+mg', 'Possible OCR error: extra zero in dosage'),
            (r'(\d)00+mg', 'Possible OCR error: multiple extra zeros'),
        ]
        
        for pattern, warning in suspicious_patterns:
            if re.search(pattern, dosage_lower):
                return True, f"CAUTION: {warning}. Please verify dosage {dosage} is correct."
        
        return True, None
    
    def extract_from_image(self, image_data: bytes) -> PrescriptionInfo:
        """
        Extract medication information from prescription image
        Uses Gemini if available, otherwise OpenAI
        """
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
            # Use Gemini Pro 1.5 (ONLY)
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(image_data))
            
            # Generate content - removed response_mime_type as it's not supported in all API versions
            response = self.model.generate_content(
                [prompt, image],
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 2000
                }
            )
            
            result_text = response.text
            result_dict = json.loads(result_text)
            
            prescription = PrescriptionInfo(**result_dict)
            
            # Validate dosage for safety (life-critical)
            if prescription.dosage:
                is_valid, warning = self._validate_dosage(prescription.dosage, prescription.medication_name)
                if not is_valid:
                    raise ValueError(f"CRITICAL: {warning} This prescription cannot be processed automatically. Please verify the image and dosage manually.")
                elif warning:
                    # Log warning but allow processing
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Dosage validation warning for {prescription.medication_name}: {warning}")
            
            return prescription
            
        except json.JSONDecodeError as e:
            # JSON parsing failed - try to extract text response
            try:
                result_text = response.text if hasattr(response, 'text') else str(response)
                # Try to extract medication name from text
                import re
                med_match = re.search(r'(?:medication|drug|prescription)[\s:]+([A-Za-z0-9\s-]+)', result_text, re.IGNORECASE)
                if med_match:
                    return PrescriptionInfo(
                        medication_name=med_match.group(1).strip(),
                        instructions=result_text[:500]  # First 500 chars
                    )
            except (AttributeError, IndexError, ValueError):
                # Regex match failed, continue to raise error
                pass
            # If extraction fails, raise the error
            raise ValueError(f"Failed to parse prescription data. The AI response was not in the expected format. Please try again with a clearer image.")
        except Exception as e:
            # Re-raise with user-friendly message
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                raise ValueError("The AI model is not available. Please check your API configuration.")
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                raise ValueError("API quota exceeded. Please try again later.")
            else:
                raise ValueError(f"Failed to extract prescription: {error_msg}. Please ensure the image is clear and contains a prescription.")
    
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

