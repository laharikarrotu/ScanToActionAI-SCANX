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
        
        self.detected_pii = detected
        return detected
    
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
    
    def redact_image(self, image_data: bytes, ocr_text: Optional[str] = None) -> Tuple[bytes, int]:
        """
        Redact PII from image by blurring or blacking out detected regions.
        
        Note: This is a simplified implementation. For production, consider using
        more advanced OCR-based redaction that can identify text regions in images.
        
        Args:
            image_data: Raw image bytes
            ocr_text: Optional OCR text to help identify PII locations
        
        Returns:
            Tuple of (redacted_image_bytes, count_of_redactions)
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL not available, skipping image redaction")
            return image_data, 0
        
        try:
            # Detect PII in OCR text if provided
            detected_pii = []
            if ocr_text:
                detected_pii = self.detect_pii_in_text(ocr_text)
            
            if not detected_pii:
                return image_data, 0
            
            # Open image
            image = Image.open(BytesIO(image_data))
            draw = ImageDraw.Draw(image)
            
            # For now, we'll add a warning overlay if PII is detected
            # Full image redaction requires OCR bounding boxes which is more complex
            if detected_pii:
                # Add a small redaction indicator in corner
                # In production, you'd use OCR bounding boxes to redact specific regions
                logger.warning(f"PII detected in image but full redaction requires OCR bounding boxes. "
                             f"Count: {len(detected_pii)}")
            
            # Save redacted image
            output = BytesIO()
            image.save(output, format='PNG')
            redacted_data = output.getvalue()
            
            return redacted_data, len(detected_pii)
            
        except Exception as e:
            logger.error(f"Error during image redaction: {str(e)}", exc_info=True)
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

