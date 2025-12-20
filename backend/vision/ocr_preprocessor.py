"""
OCR Preprocessing - Extracts text using OCR before LLM analysis
"""
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np
from typing import Optional, Dict, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.pii_redaction import PIIRedactor
    PII_REDACTION_AVAILABLE = True
except ImportError:
    PII_REDACTION_AVAILABLE = False
    PIIRedactor = None

class OCRPreprocessor:
    """Preprocesses images and extracts text using OCR"""
    
    def __init__(self, enable_pii_redaction: bool = True):
        """
        Initialize OCR Preprocessor.
        
        Args:
            enable_pii_redaction: If True, automatically redact PII from extracted text
        """
        self.enable_pii_redaction = enable_pii_redaction and PII_REDACTION_AVAILABLE
        if self.enable_pii_redaction:
            self.pii_redactor = PIIRedactor(redaction_mode="blur")
        else:
            self.pii_redactor = None
    
    @staticmethod
    def preprocess_image(image_data: bytes) -> bytes:
        """
        Enhance image quality for better OCR and LLM analysis
        
        Steps:
        1. Increase contrast
        2. Sharpen text
        3. Denoise
        4. Convert to optimal format
        """
        try:
            # Convert to PIL Image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to OpenCV format (numpy array)
            img_array = np.array(img)
            
            # Convert RGB to BGR if needed (OpenCV uses BGR)
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                # Check if it's RGB (PIL default) or BGR
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale for processing
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array
            
            # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Sharpen image
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(sharpened, h=10)
            
            # Convert back to RGB for PIL
            if len(img_array.shape) == 3:
                # Convert back to color
                denoised_color = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)
                final_img = Image.fromarray(cv2.cvtColor(denoised_color, cv2.COLOR_BGR2RGB))
            else:
                final_img = Image.fromarray(denoised)
            
            # Convert back to bytes
            output = io.BytesIO()
            final_img.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            # If preprocessing fails, return original
            import logging
            logging.warning(f"Image preprocessing failed: {str(e)}, using original image")
            return image_data
    
    def extract_text(self, image_data: bytes, preprocess: bool = True) -> Dict[str, any]:
        """
        Extract text from image using OCR
        
        Args:
            image_data: Image bytes
            preprocess: Whether to preprocess image first
        
        Returns:
            {
                "text": str,
                "confidence": float,
                "word_count": int,
                "lines": List[str]
            }
        """
        try:
            # Preprocess if requested
            processed_data = OCRPreprocessor.preprocess_image(image_data) if preprocess else image_data
            
            # Open image
            img = Image.open(io.BytesIO(processed_data))
            
            # Extract text with confidence scores
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            # Extract text lines
            text_lines = []
            current_line = []
            current_y = None
            
            for i, word in enumerate(ocr_data['text']):
                if word.strip():  # Non-empty word
                    y_pos = ocr_data['top'][i]
                    conf = ocr_data['conf'][i]
                    
                    # Group words on same line
                    if current_y is None or abs(y_pos - current_y) < 10:
                        current_line.append((word, conf))
                        current_y = y_pos
                    else:
                        if current_line:
                            text_lines.append(current_line)
                        current_line = [(word, conf)]
                        current_y = y_pos
            
            # Add last line
            if current_line:
                text_lines.append(current_line)
            
            # Build full text
            full_text = '\n'.join([' '.join([w[0] for w in line]) for line in text_lines])
            
            # Calculate average confidence
            all_confs = [conf for line in text_lines for _, conf in line if conf > 0]
            avg_confidence = sum(all_confs) / len(all_confs) if all_confs else 0.0
            
            # Count words
            word_count = len([w for line in text_lines for w, _ in line])
            
            # Redact PII if enabled
            redacted_text = full_text
            pii_count = 0
            pii_summary = {}
            if self.enable_pii_redaction and self.pii_redactor:
                redacted_text, pii_count = self.pii_redactor.redact_text(full_text)
                if pii_count > 0:
                    pii_summary = self.pii_redactor.get_redaction_summary()
                    import logging
                    logging.warning(f"PII detected and redacted: {pii_count} instances", 
                                  context={"pii_summary": pii_summary})
            
            return {
                "text": redacted_text,
                "original_text": full_text if self.enable_pii_redaction else None,  # Keep original for internal use only
                "confidence": avg_confidence,
                "word_count": word_count,
                "lines": [' '.join([w[0] for w in line]) for line in text_lines],
                "pii_detected": pii_count > 0,
                "pii_count": pii_count,
                "pii_summary": pii_summary
            }
            
        except Exception as e:
            import logging
            logging.error(f"OCR extraction failed: {str(e)}")
            return {
                "text": "",
                "original_text": None,
                "confidence": 0.0,
                "word_count": 0,
                "lines": [],
                "pii_detected": False,
                "pii_count": 0,
                "pii_summary": {}
            }

