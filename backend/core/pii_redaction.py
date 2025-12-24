"""
PII (Personally Identifiable Information) Redaction Module

Automatically detects and redacts PII from document images before sending to external LLM APIs.
This is critical for HIPAA compliance and data privacy.
"""
import re
import logging
from typing import Dict, List, Tuple, Optional
import base64
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class PIIRedactor:
    """
    Detects and redacts PII from images and text.
    
    Supports:
    - SSN (Social Security Numbers)
    - Phone numbers
    - Email addresses
    - Credit card numbers
    - Medical record numbers
    - Patient names (via OCR + pattern matching)
    """
    
    # Regex patterns for PII detection
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\(\d{3}\)\s?\d{3}-\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b')
    MEDICAL_RECORD_PATTERN = re.compile(r'\bMRN[:\s]?\d{6,}\b|\bMedical Record[:\s]?#?\d{6,}\b', re.IGNORECASE)
    
    # Common medical PII patterns
    DATE_OF_BIRTH_PATTERN = re.compile(r'\b(?:DOB|Date of Birth|Birth Date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', re.IGNORECASE)
    
    # Patient name patterns (common medical document formats)
    # Pattern 1: "Patient Name: John Doe" or "Name: John Doe"
    PATIENT_NAME_PATTERN_1 = re.compile(r'\b(?:Patient\s+)?Name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', re.IGNORECASE)
    # Pattern 2: "Dr. Smith's patient John Doe" or "patient John Doe"
    PATIENT_NAME_PATTERN_2 = re.compile(r'\b(?:patient|pt\.?)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', re.IGNORECASE)
    # Pattern 3: Common name format after titles (Dr., Mr., Mrs., Ms.)
    PATIENT_NAME_PATTERN_3 = re.compile(r'\b(?:Dr\.|Mr\.|Mrs\.|Ms\.|Miss)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', re.IGNORECASE)
    
    # Common medical terms to avoid false positives (whitelist)
    MEDICAL_TERMS_WHITELIST = {
        'tylenol', 'aspirin', 'ibuprofen', 'advil', 'motrin', 'aleve',
        'prescription', 'medication', 'dosage', 'frequency', 'quantity',
        'pharmacy', 'pharmacist', 'doctor', 'physician', 'nurse',
        'hospital', 'clinic', 'medical', 'health', 'patient', 'care'
    }
    
    def __init__(self, redaction_mode: str = "blur"):
        """
        Initialize PII Redactor.
        
        Args:
            redaction_mode: "blur" (default) or "blackout" - how to redact detected PII
        """
        self.redaction_mode = redaction_mode
        self.detected_pii: List[Dict[str, str]] = []
    
    def detect_pii_in_text(self, text: str) -> List[Dict[str, str]]:
        """
        Detect PII patterns in text.
        
        Returns:
            List of detected PII with type and value
        """
        detected = []
        
        # SSN
        for match in self.SSN_PATTERN.finditer(text):
            detected.append({
                "type": "SSN",
                "value": match.group(),
                "position": match.span()
            })
        
        # Phone numbers
        for match in self.PHONE_PATTERN.finditer(text):
            detected.append({
                "type": "PHONE",
                "value": match.group(),
                "position": match.span()
            })
        
        # Email addresses
        for match in self.EMAIL_PATTERN.finditer(text):
            detected.append({
                "type": "EMAIL",
                "value": match.group(),
                "position": match.span()
            })
        
        # Credit card numbers
        for match in self.CREDIT_CARD_PATTERN.finditer(text):
            detected.append({
                "type": "CREDIT_CARD",
                "value": match.group(),
                "position": match.span()
            })
        
        # Medical record numbers
        for match in self.MEDICAL_RECORD_PATTERN.finditer(text):
            detected.append({
                "type": "MEDICAL_RECORD",
                "value": match.group(),
                "position": match.span()
            })
        
        # Date of birth
        for match in self.DATE_OF_BIRTH_PATTERN.finditer(text):
            detected.append({
                "type": "DOB",
                "value": match.group(1),
                "position": match.span()
            })
        
        # Patient names (pattern-based detection)
        # This is a simplified approach - for production, use NLP-based NER
        detected_names = []
        
        # Pattern 1: "Patient Name: John Doe"
        for match in self.PATIENT_NAME_PATTERN_1.finditer(text):
            name = match.group(1).strip()
            if self._is_likely_name(name):
                detected_names.append({
                    "type": "PATIENT_NAME",
                    "value": name,
                    "position": match.span()
                })
        
        # Pattern 2: "patient John Doe"
        for match in self.PATIENT_NAME_PATTERN_2.finditer(text):
            name = match.group(1).strip()
            if self._is_likely_name(name):
                detected_names.append({
                    "type": "PATIENT_NAME",
                    "value": name,
                    "position": match.span()
                })
        
        # Pattern 3: "Dr. John Doe" (if not a medication/prescriber context)
        for match in self.PATIENT_NAME_PATTERN_3.finditer(text):
            name = match.group(1).strip()
            # Check context - if followed by medication-related terms, might be prescriber, not patient
            context_start = match.end()
            context = text[context_start:context_start+50].lower()
            if not any(term in context for term in ['prescribe', 'medication', 'dosage', 'mg', 'ml']):
                if self._is_likely_name(name):
                    detected_names.append({
                        "type": "PATIENT_NAME",
                        "value": name,
                        "position": match.span()
                    })
        
        # Add detected names (avoid duplicates)
        for name_pii in detected_names:
            # Check if this name was already detected
            if not any(p["value"].lower() == name_pii["value"].lower() for p in detected):
                detected.append(name_pii)
        
        self.detected_pii = detected
        return detected
    
    def _is_likely_name(self, text: str) -> bool:
        """
        Heuristic to determine if text is likely a person's name.
        
        Rules:
        - 2-4 words (first name + last name, possibly middle)
        - Each word starts with capital letter
        - Not in medical terms whitelist
        - Not all caps (likely not an acronym)
        - Contains letters (not just numbers/symbols)
        """
        words = text.split()
        
        # Must be 2-4 words
        if len(words) < 2 or len(words) > 4:
            return False
        
        # Check if all words start with capital letter
        if not all(word and word[0].isupper() for word in words):
            return False
        
        # Check if it's all caps (likely acronym)
        if text.isupper() and len(text) < 10:
            return False
        
        # Check if it's in medical terms whitelist
        text_lower = text.lower()
        if any(term in text_lower for term in self.MEDICAL_TERMS_WHITELIST):
            return False
        
        # Must contain letters
        if not any(c.isalpha() for c in text):
            return False
        
        # Each word should be 2+ characters
        if not all(len(word) >= 2 for word in words):
            return False
        
        return True
    
    def redact_text(self, text: str, detected_pii: Optional[List[Dict[str, str]]] = None) -> Tuple[str, int]:
        """
        Redact PII from text by replacing with [REDACTED].
        
        Returns:
            Tuple of (redacted_text, count_of_redactions)
        """
        if detected_pii is None:
            detected_pii = self.detect_pii_in_text(text)
        
        if not detected_pii:
            return text, 0
        
        # Sort by position (descending) to redact from end to start
        sorted_pii = sorted(detected_pii, key=lambda x: x["position"][0], reverse=True)
        
        redacted_text = text
        redaction_count = 0
        
        for pii in sorted_pii:
            start, end = pii["position"]
            redacted_text = redacted_text[:start] + f"[REDACTED_{pii['type']}]" + redacted_text[end:]
            redaction_count += 1
        
        logger.info(f"Redacted {redaction_count} PII instances from text", 
                   context={"pii_count": redaction_count, "types": [p["type"] for p in detected_pii]})
        
        return redacted_text, redaction_count
    
    def redact_image(self, image_data: bytes, ocr_text: Optional[str] = None, use_ocr: bool = True) -> Tuple[bytes, int]:
        """
        Redact PII from image by blurring or blacking out detected regions.
        
        Uses OCR to find text regions containing PII and redacts them.
        
        Args:
            image_data: Raw image bytes
            ocr_text: Optional OCR text to help identify PII locations
            use_ocr: If True, use OCR to find text regions (default: True)
        
        Returns:
            Tuple of (redacted_image_bytes, count_of_redactions)
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL not available, skipping image redaction")
            return image_data, 0
        
        try:
            # Open image
            image = Image.open(BytesIO(image_data))
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Detect PII in OCR text if provided
            detected_pii = []
            if ocr_text:
                detected_pii = self.detect_pii_in_text(ocr_text)
            
            # If no PII detected, return original
            if not detected_pii:
                return image_data, 0
            
            # Use OCR to find text regions if available
            text_regions_to_redact = []
            
            if use_ocr:
                try:
                    import pytesseract
                    # Get OCR data with bounding boxes
                    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                    
                    # Find text regions that contain PII
                    for i, text in enumerate(ocr_data.get('text', [])):
                        if text and text.strip():
                            # Check if this text contains any detected PII
                            for pii in detected_pii:
                                pii_value = pii.get('value', '')
                                # Check if PII value appears in this text region
                                if pii_value.lower() in text.lower() or text.lower() in pii_value.lower():
                                    # Get bounding box for this text
                                    x = ocr_data.get('left', [0])[i]
                                    y = ocr_data.get('top', [0])[i]
                                    w = ocr_data.get('width', [0])[i]
                                    h = ocr_data.get('height', [0])[i]
                                    
                                    if w > 0 and h > 0:
                                        # Expand region slightly for better redaction
                                        padding = 5
                                        text_regions_to_redact.append({
                                            'x': max(0, x - padding),
                                            'y': max(0, y - padding),
                                            'width': min(width - x, w + 2 * padding),
                                            'height': min(height - y, h + 2 * padding),
                                            'pii_type': pii.get('type', 'UNKNOWN')
                                        })
                                    break
                except ImportError:
                    logger.warning("pytesseract not available, using fallback redaction method")
                    use_ocr = False
                except Exception as e:
                    logger.warning(f"OCR redaction failed: {e}, using fallback method")
                    use_ocr = False
            
            # If OCR didn't find regions, use fallback: redact entire image if PII detected
            if not text_regions_to_redact and detected_pii:
                logger.warning(f"PII detected but OCR regions not found. Using conservative approach: "
                             f"redacting entire image to protect privacy.")
                # Redact entire image as safety measure
                if self.redaction_mode == "blur":
                    # Blur entire image
                    from PIL import ImageFilter
                    image = image.filter(ImageFilter.GaussianBlur(radius=20))
                else:
                    # Blackout entire image
                    draw.rectangle([(0, 0), (width, height)], fill='black')
            
            # Redact detected text regions
            redaction_count = 0
            for region in text_regions_to_redact:
                x = region['x']
                y = region['y']
                w = region['width']
                h = region['height']
                
                if self.redaction_mode == "blur":
                    # Extract region, blur it, paste back
                    region_img = image.crop((x, y, x + w, y + h))
                    from PIL import ImageFilter
                    blurred_region = region_img.filter(ImageFilter.GaussianBlur(radius=10))
                    image.paste(blurred_region, (x, y))
                else:
                    # Blackout region
                    draw.rectangle([(x, y), (x + w, y + h)], fill='black')
                
                redaction_count += 1
                logger.info(f"Redacted {region['pii_type']} at ({x}, {y})")
            
            # Save redacted image
            output = BytesIO()
            # Preserve original format if possible
            try:
                format_name = image.format or 'PNG'
                image.save(output, format=format_name)
            except:
                # Fallback to PNG
                image.save(output, format='PNG')
            
            redacted_data = output.getvalue()
            
            logger.info(f"Image redaction complete: {redaction_count} regions redacted, {len(detected_pii)} PII types detected")
            
            return redacted_data, redaction_count
            
        except Exception as e:
            logger.error(f"Error during image redaction: {str(e)}", exc_info=True)
            # If redaction fails, return original (better than crashing)
            # But log the error for security audit
            return image_data, 0
    
    def should_redact(self, text: str) -> bool:
        """
        Quick check if text contains PII.
        
        Returns:
            True if PII detected, False otherwise
        """
        detected = self.detect_pii_in_text(text)
        return len(detected) > 0
    
    def get_redaction_summary(self) -> Dict[str, int]:
        """
        Get summary of detected PII types.
        
        Returns:
            Dictionary mapping PII type to count
        """
        summary = {}
        for pii in self.detected_pii:
            pii_type = pii["type"]
            summary[pii_type] = summary.get(pii_type, 0) + 1
        return summary

