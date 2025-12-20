"""
Gemini Vision Engine - Alternative to OpenAI for vision analysis
Uses Google Gemini Pro 1.5 for image understanding
"""
import base64
from typing import Optional, Dict, Any
import os
import json
import re
from vision.ui_detector import UIElement, UISchema
from vision.ocr_preprocessor import OCRPreprocessor

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

class GeminiVisionEngine:
    """Vision engine using Google Gemini Pro 1.5"""
    
    def __init__(self, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.ocr_preprocessor = OCRPreprocessor()
    
    def analyze_image(
        self,
        image_data: bytes,
        hint: Optional[str] = None
    ) -> UISchema:
        """
        Analyze image using Gemini Pro 1.5 Vision
        """
        # Preprocess image
        try:
            processed_image = self.ocr_preprocessor.preprocess_image(image_data)
        except:
            processed_image = image_data
        
        # Extract OCR text
        ocr_result = self.ocr_preprocessor.extract_text(processed_image, preprocess=False)
        ocr_text = ocr_result.get("text", "")
        
        # Identify document type
        doc_type = self._identify_document_type(processed_image, ocr_text)
        
        # Build prompt
        prompt = self._build_prompt(doc_type, ocr_text, hint)
        
        try:
            # Convert image to format Gemini expects
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(processed_image))
            
            # Call Gemini
            response = self.model.generate_content(
                [prompt, image],
                generation_config={
                    "temperature": 0.0,
                    "max_output_tokens": 4000,
                }
            )
            
            result_text = response.text
            
            # Parse JSON from response
            try:
                result_dict = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                if json_match:
                    result_dict = json.loads(json_match.group(1))
                else:
                    raise ValueError("Could not parse JSON from Gemini response")
            
            # Convert to UISchema
            elements = []
            for elem in result_dict.get("elements", []):
                try:
                    if not elem.get("id"):
                        elem["id"] = f"elem_{len(elements)}"
                    if not elem.get("type"):
                        elem["type"] = "text"
                    if not elem.get("label"):
                        elem["label"] = elem.get("value", "") or "Unknown"
                    elements.append(UIElement(**elem))
                except Exception:
                    elements.append(UIElement(
                        id=f"elem_{len(elements)}",
                        type="text",
                        label=str(elem.get("label", elem.get("value", "Unknown")))
                    ))
            
            # Fallback: Create elements from OCR if none found
            if not elements and ocr_text:
                ocr_lines = [line.strip() for line in ocr_text.split('\n') if line.strip()][:10]
                for i, line in enumerate(ocr_lines):
                    elements.append(UIElement(
                        id=f"ocr_text_{i}",
                        type="text",
                        label=line
                    ))
            
            return UISchema(
                page_type=result_dict.get("page_type", doc_type),
                url_hint=result_dict.get("url_hint"),
                elements=elements
            )
            
        except Exception as e:
            import logging
            logging.error(f"Gemini vision error: {str(e)}", exc_info=True)
            
            # Fallback: Create elements from OCR
            elements = []
            if ocr_text:
                ocr_lines = [line.strip() for line in ocr_text.split('\n') if line.strip()][:10]
                for i, line in enumerate(ocr_lines):
                    elements.append(UIElement(
                        id=f"ocr_text_{i}",
                        type="text",
                        label=line
                    ))
            
            return UISchema(
                page_type=doc_type,
                url_hint=None,
                elements=elements if elements else [UIElement(id="elem_0", type="text", label="Document detected")]
            )
    
    def _identify_document_type(self, image_data: bytes, ocr_text: str) -> str:
        """Identify document type using Gemini"""
        try:
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(image_data))
            
            prompt = f"""Analyze this medical document image and identify its type.

OCR Text: {ocr_text[:500] if ocr_text else "No text extracted"}

Return ONLY one word: prescription, medical_form, insurance_card, appointment_page, lab_result, medical_record, or other"""
            
            response = self.model.generate_content([prompt, image])
            doc_type = response.text.strip().lower()
            
            valid_types = ["prescription", "medical_form", "insurance_card", "appointment_page", "lab_result", "medical_record", "other"]
            if doc_type in valid_types:
                return doc_type
            return "other"
        except:
            return "other"
    
    def _build_prompt(self, doc_type: str, ocr_text: str, hint: Optional[str]) -> str:
        """Build analysis prompt for Gemini"""
        prompt = f"""Analyze this {doc_type} image and extract all UI elements, text, and structured data.

Return a JSON object with this EXACT structure:
{{
  "page_type": "{doc_type}",
  "url_hint": "guessed URL if visible, or null",
  "elements": [
    {{
      "id": "unique_id_1",
      "type": "text" | "medication" | "dosage" | "prescriber" | "pharmacy" | "label" | "data" | "heading" | "instruction" | "warning" | "button" | "input" | "link",
      "label": "EXTRACT THIS TEXT - visible text or label (REQUIRED)",
      "value": "current value if input/data field, or null",
      "position": {{"x": 100, "y": 200}} or null
    }}
  ]
}}

CRITICAL RULES:
1. The "elements" array MUST NOT be empty - extract at least 3-10 elements
2. Extract EVERY piece of visible text as a separate element
3. For each line of text, create an element with type="text" and label="the text content"
4. If you see medication names, create elements with type="medication"
5. If OCR extracted text, use it to create elements even if you can't see it clearly
6. NEVER return an empty elements array - if you see ANY text, create elements for it

OCR Extracted Text (use this to help):
{ocr_text[:1500] if ocr_text else "No OCR text available"}

{f"User Context: {hint}" if hint else ""}

Return ONLY valid JSON, no other text."""
        return prompt

