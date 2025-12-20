"""
Vision Engine - Uses multimodal LLM with OCR preprocessing and multi-step detection
"""
import base64
import json
import re
from typing import Optional, Dict, Any
from openai import OpenAI
from pydantic import BaseModel
import os
from vision.ocr_preprocessor import OCRPreprocessor

class UIElement(BaseModel):
    id: str
    type: str  # button, input, text, link, etc.
    label: str
    value: Optional[str] = None
    position: Optional[Dict[str, int]] = None
    confidence: Optional[float] = None  # 0.0 to 1.0, higher = more confident

class UISchema(BaseModel):
    page_type: str
    url_hint: Optional[str] = None
    elements: list[UIElement]

class VisionEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # GPT-4o with medical fine-tuning via prompts
        self.ocr_preprocessor = OCRPreprocessor()
    
    def _identify_document_type(self, image_data: bytes, ocr_text: str) -> str:
        """
        Step 1: Identify document type using lightweight analysis
        """
        try:
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            type_prompt = f"""Analyze this medical document image and identify its type.

OCR Extracted Text (may be incomplete):
{ocr_text[:500] if ocr_text else "No text extracted"}

What type of medical document is this?
- prescription (medication bottle/label)
- medical_form (patient intake form, registration)
- insurance_card (health insurance card)
- appointment_page (booking page, schedule)
- lab_result (test results, lab report)
- medical_record (doctor notes, diagnosis)
- other

Return ONLY the document type as a single word (e.g., "prescription", "medical_form", etc.)"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": type_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.0,
                max_tokens=50
            )
            
            doc_type = response.choices[0].message.content.strip().lower()
            # Clean up response
            doc_type = doc_type.replace('"', '').replace("'", "").strip()
            return doc_type if doc_type in ["prescription", "medical_form", "insurance_card", "appointment_page", "lab_result", "medical_record", "other"] else "other"
            
        except Exception as e:
            import logging
            logging.warning(f"Document type identification failed: {str(e)}")
            return "other"
    
    def _get_medical_prompt(self, doc_type: str, ocr_text: str) -> str:
        """
        Get medical-specific prompt based on document type
        """
        base_prompt = """You are a medical document analysis expert with specialized training in healthcare documentation. 
Analyze this healthcare image with extreme precision and extract ALL visible text, fields, and elements.

MEDICAL TERMINOLOGY EXPERTISE:
- Recognize medication names (generic and brand)
- Understand dosage formats (mg, ml, units, percentages)
- Identify medical abbreviations (BID, TID, QID, PRN, etc.)
- Extract prescription numbers, DEA numbers, NDC codes
- Recognize medical conditions and diagnoses
- Understand insurance terminology (member ID, group number, policy numbers)

"""
        
        if doc_type == "prescription":
            return base_prompt + """PRESCRIPTION-SPECIFIC EXTRACTION:
Extract EVERY detail from this prescription label/bottle:

1. Medication Information:
   - Brand name (e.g., "Tylenol", "Advil")
   - Generic name (e.g., "acetaminophen", "ibuprofen")
   - Strength/dosage (e.g., "500mg", "10mg/5ml", "0.5%")
   - Form (tablet, capsule, liquid, cream, etc.)
   - Quantity (e.g., "#30", "90 tablets", "4 fl oz")

2. Instructions:
   - Frequency (e.g., "twice daily", "every 6 hours", "as needed")
   - Route (e.g., "by mouth", "topically", "inject")
   - Special instructions (e.g., "with food", "on empty stomach")
   - Duration if specified

3. Prescriber Information:
   - Doctor name
   - DEA number
   - Prescription number
   - Date prescribed

4. Pharmacy Information:
   - Pharmacy name
   - Pharmacy address/phone
   - NDC number
   - Expiration date
   - Refill information

5. Warnings and Precautions:
   - All warning labels
   - Side effects mentioned
   - Storage instructions
   - Age restrictions

OCR Extracted Text (use as reference):
""" + (ocr_text[:1000] if ocr_text else "No OCR text available") + """

CRITICAL: Extract EVERY piece of text, even if partially visible. Medical accuracy is life-critical."""
        
        elif doc_type == "medical_form":
            return base_prompt + """MEDICAL FORM EXTRACTION:
Extract all form fields, labels, and information:

1. Patient Information Fields:
   - Name, DOB, SSN, address, phone
   - Insurance information
   - Emergency contact

2. Medical History Fields:
   - Allergies
   - Current medications
   - Past surgeries
   - Chronic conditions
   - Family history

3. Current Visit Information:
   - Chief complaint
   - Symptoms
   - Vital signs fields
   - Assessment fields

4. All form elements:
   - Input fields (even if empty - extract the label)
   - Checkboxes
   - Radio buttons
   - Dropdowns
   - Buttons (Submit, Save, etc.)

OCR Extracted Text:
""" + (ocr_text[:1000] if ocr_text else "No OCR text available") + """
"""
        
        elif doc_type == "insurance_card":
            return base_prompt + """INSURANCE CARD EXTRACTION:
Extract all information from the insurance card:

- Member name
- Member ID number
- Group number
- Policy number
- Insurance company name
- Plan type
- Effective dates
- Phone numbers
- Website URLs

OCR Extracted Text:
""" + (ocr_text[:1000] if ocr_text else "No OCR text available") + """
"""
        
        else:
            return base_prompt + f"""Extract ALL text and elements from this {doc_type.replace('_', ' ')}.

OCR Extracted Text (use as reference):
""" + (ocr_text[:1000] if ocr_text else "No OCR text available") + """

Extract every visible piece of information."""
    
    def analyze_image(self, image_data: bytes, hint: Optional[str] = None) -> UISchema:
        """
        Multi-step analysis with OCR preprocessing:
        1. Preprocess image (enhance quality)
        2. Extract text using OCR
        3. Identify document type
        4. Extract details using type-specific prompts
        """
        # Step 1: Preprocess image for better quality
        try:
            processed_image = self.ocr_preprocessor.preprocess_image(image_data)
        except:
            processed_image = image_data  # Use original if preprocessing fails
        
        # Step 2: Extract text using OCR
        ocr_result = self.ocr_preprocessor.extract_text(processed_image, preprocess=False)
        ocr_text = ocr_result.get("text", "")
        
        # Step 3: Identify document type (multi-step detection)
        doc_type = self._identify_document_type(processed_image, ocr_text)
        
        # Step 4: Get type-specific medical prompt
        prompt = self._get_medical_prompt(doc_type, ocr_text)
        
        # Add OCR context to prompt
        if ocr_text:
            prompt += f"\n\nOCR has extracted the following text (use this to help identify elements):\n{ocr_text[:1500]}\n\n"
        
        # Add user hint if provided
        if hint:
            prompt += f"\n\nUser Context: {hint}\n"
        
        # Add JSON structure requirements
        prompt += """
CRITICAL: You MUST return a JSON object with this EXACT structure. The "elements" array MUST contain at least one element - even if it's just text.

{
  "page_type": \"""" + doc_type + """\",
  "url_hint": "guessed URL if visible, or null",
  "elements": [
    {
      "id": "unique_id_1",
      "type": "text" | "medication" | "dosage" | "prescriber" | "pharmacy" | "label" | "data" | "heading" | "instruction" | "warning" | "button" | "input" | "link" | "select" | "checkbox" | "radio",
      "label": "EXTRACT THIS TEXT - visible text or label (REQUIRED - never leave empty, use OCR text if needed)",
      "value": "current value if input/select/data field, or null",
      "position": {"x": 100, "y": 200} or null
    }
  ]
}

MANDATORY RULES:
1. The "elements" array MUST NOT be empty - extract at least 3-10 elements
2. Extract EVERY piece of visible text as a separate element
3. For each line of text, create an element with type="text" and label="the text content"
4. If you see medication names, create elements with type="medication"
5. If OCR extracted text, use it to create elements even if you can't see it clearly in the image
6. If the image is a prescription, extract: medication name, dosage, instructions, prescriber name, pharmacy name
7. If the image is a form, extract: all field labels, all visible text, all buttons
8. NEVER return an empty elements array - if you see ANY text, create elements for it

EXAMPLE for a prescription:
{
  "page_type": "prescription",
  "elements": [
    {"id": "1", "type": "medication", "label": "Tylenol 500mg", "value": null},
    {"id": "2", "type": "dosage", "label": "Take 2 tablets every 6 hours", "value": null},
    {"id": "3", "type": "prescriber", "label": "Dr. Smith", "value": null},
    {"id": "4", "type": "pharmacy", "label": "CVS Pharmacy", "value": null}
  ]
}

If you cannot see the image clearly, use the OCR text to create elements:
{
  "page_type": "prescription",
  "elements": [
    {"id": "1", "type": "text", "label": "First line of OCR text", "value": null},
    {"id": "2", "type": "text", "label": "Second line of OCR text", "value": null}
  ]
}
"""
        
        # Convert processed image to base64
        image_base64 = base64.b64encode(processed_image).decode('utf-8')
        
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
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"  # High detail for medical documents
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.0,  # Deterministic for medical accuracy
                max_tokens=4000  # Allow detailed extraction
            )
            
            result_text = response.choices[0].message.content
            import logging
            
            # Log the raw response for debugging
            logging.info(f"Raw OpenAI response: {result_text[:500]}")
            
            result_dict = json.loads(result_text)
            
            # Log parsed result
            logging.info(f"Parsed elements count: {len(result_dict.get('elements', []))}")
            
            # Convert to UISchema - handle missing fields gracefully
            elements = []
            for elem in result_dict.get("elements", []):
                try:
                    # Ensure required fields exist
                    if not elem.get("id"):
                        elem["id"] = f"elem_{len(elements)}"
                    if not elem.get("type"):
                        elem["type"] = "text"
                    if not elem.get("label"):
                        elem["label"] = elem.get("value", "") or "Unknown"
                    
                    elements.append(UIElement(**elem))
                except Exception as elem_error:
                    logging.warning(f"Failed to parse element: {elem}, error: {str(elem_error)}")
                    # Create a fallback element
                    elements.append(UIElement(
                        id=f"elem_{len(elements)}",
                        type="text",
                        label=str(elem.get("label", elem.get("value", "Unknown")))
                    ))
            
            # If no elements found, try to extract at least text from OCR
            if not elements and ocr_text:
                logging.warning("No elements found, creating elements from OCR text")
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
            
        except json.JSONDecodeError as e:
            import logging
            logging.error(f"JSON decode error: {str(e)}, response: {result_text[:500] if 'result_text' in locals() else 'N/A'}")
            # Try to extract JSON from response if it's wrapped in markdown
            try:
                if 'result_text' in locals():
                    # Try to find JSON in markdown code blocks
                    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                    if json_match:
                        result_dict = json.loads(json_match.group(1))
                        elements = [UIElement(**elem) for elem in result_dict.get("elements", [])]
                        return UISchema(
                            page_type=result_dict.get("page_type", doc_type),
                            url_hint=result_dict.get("url_hint"),
                            elements=elements
                        )
            except:
                pass
            
        except Exception as e:
            import logging
            logging.error(f"Vision engine error: {str(e)}", exc_info=True)
            
            # Fallback: Try simpler extraction with explicit OCR-based elements
            try:
                fallback_prompt = f"""Extract ALL text and elements from this {doc_type.replace('_', ' ')}. 

OCR Extracted Text:
{ocr_text[:1000] if ocr_text else "No OCR text available"}

CRITICAL: You MUST return a JSON object with an "elements" array containing at least 3 elements.
Even if the image is unclear, use the OCR text above to create elements.

Return JSON in this format:
{{
  "page_type": "{doc_type}",
  "url_hint": null,
  "elements": [
    {{"id": "1", "type": "text", "label": "First line from OCR", "value": null}},
    {{"id": "2", "type": "text", "label": "Second line from OCR", "value": null}},
    {{"id": "3", "type": "text", "label": "Third line from OCR", "value": null}}
  ]
}}

The elements array MUST NOT be empty. Use the OCR text to create at least 3-5 text elements."""
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": fallback_prompt},
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
                    temperature=0.0,
                    max_tokens=2000
                )
                result_text = response.choices[0].message.content
                result_dict = json.loads(result_text)
                elements = [UIElement(**elem) for elem in result_dict.get("elements", [])]
                return UISchema(
                    page_type=result_dict.get("page_type", doc_type),
                    url_hint=result_dict.get("url_hint"),
                    elements=elements
                )
            except Exception as fallback_error:
                import logging
                logging.error(f"Fallback extraction also failed: {str(fallback_error)}")
                
                # Final fallback: Create elements from OCR text
                elements = []
                if ocr_text:
                    ocr_lines = [line.strip() for line in ocr_text.split('\n') if line.strip()][:15]
                    for i, line in enumerate(ocr_lines):
                        if line and len(line) > 2:  # Only add meaningful lines
                            elements.append(UIElement(
                                id=f"ocr_fallback_{i}",
                                type="text",
                                label=line[:200]  # Limit label length
                            ))
                
                # If still no elements, create at least one placeholder
                if not elements:
                    elements.append(UIElement(
                        id="placeholder_1",
                        type="text",
                        label="Image received but could not extract text. Please try a clearer image."
                    ))
                
                return UISchema(
                    page_type=doc_type,
                    elements=elements,
                    url_hint=None
                )
