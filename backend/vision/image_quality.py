"""
Image Quality Validation - Checks if image is too blurry for human eye
"""
import cv2
import numpy as np
from PIL import Image
import io
from typing import Tuple, Dict

class ImageQualityChecker:
    """Validates image quality before processing"""
    
    @staticmethod
    def check_blur(image_data: bytes, threshold: float = 100.0) -> Tuple[bool, float, str]:
        """
        Check if image is too blurry using Laplacian variance
        
        Args:
            image_data: Image bytes
            threshold: Blur threshold (lower = stricter). Default 100 is reasonable.
                      For very strict: 150-200
                      For lenient: 50-80
        
        Returns:
            (is_acceptable, blur_score, message)
        """
        try:
            # Convert bytes to numpy array
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Calculate Laplacian variance (measure of sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Determine if acceptable
            is_acceptable = laplacian_var >= threshold
            
            if is_acceptable:
                message = f"Image quality is good (sharpness score: {laplacian_var:.1f})"
            else:
                message = f"Image is too blurry. Please take a clearer photo. (sharpness score: {laplacian_var:.1f}, minimum required: {threshold})"
            
            return is_acceptable, float(laplacian_var), message
            
        except Exception as e:
            # If we can't check, allow it but warn
            return True, 0.0, f"Could not check image quality: {str(e)}"
    
    @staticmethod
    def check_resolution(image_data: bytes, min_width: int = 200, min_height: int = 200) -> Tuple[bool, str]:
        """
        Check if image has minimum resolution
        
        Args:
            image_data: Image bytes
            min_width: Minimum width in pixels
            min_height: Minimum height in pixels
        
        Returns:
            (is_acceptable, message)
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size
            
            if width >= min_width and height >= min_height:
                return True, f"Resolution OK ({width}x{height})"
            else:
                return False, f"Image too small ({width}x{height}). Minimum: {min_width}x{min_height}"
                
        except Exception as e:
            return True, f"Could not check resolution: {str(e)}"
    
    @staticmethod
    def check_brightness(image_data: bytes, min_brightness: float = 20.0, max_brightness: float = 240.0) -> Tuple[bool, str]:
        """
        Check if image is too dark or too bright
        More lenient thresholds for medical documents (OCR can handle varied lighting)
        
        Args:
            image_data: Image bytes
            min_brightness: Minimum average brightness (0-255) - lowered to 20 for leniency
            max_brightness: Maximum average brightness (0-255) - raised to 240 for leniency
        
        Returns:
            (is_acceptable, message)
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
            
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            avg_brightness = np.mean(gray)
            
            if min_brightness <= avg_brightness <= max_brightness:
                return True, f"Brightness OK ({avg_brightness:.1f})"
            elif avg_brightness < min_brightness:
                # Very dark images - still allow but warn (OCR preprocessing can help)
                if avg_brightness < 10:
                    return False, f"Image is extremely dark (brightness: {avg_brightness:.1f}). Please use better lighting or a flash."
                else:
                    # Moderately dark - allow but note it might affect accuracy
                    return True, f"Image is somewhat dark (brightness: {avg_brightness:.1f}), but will attempt processing."
            else:
                # Very bright images - still allow but warn
                if avg_brightness > 250:
                    return False, f"Image is extremely bright (brightness: {avg_brightness:.1f}). Please reduce glare or shadows."
                else:
                    return True, f"Image is somewhat bright (brightness: {avg_brightness:.1f}), but will attempt processing."
                
        except Exception as e:
            return True, f"Could not check brightness: {str(e)}"
    
    @staticmethod
    def validate_image(image_data: bytes) -> Dict[str, any]:
        """
        Comprehensive image quality validation
        
        Returns:
            {
                "is_valid": bool,
                "blur_check": {"passed": bool, "score": float, "message": str},
                "resolution_check": {"passed": bool, "message": str},
                "brightness_check": {"passed": bool, "message": str},
                "overall_message": str
            }
        """
        blur_passed, blur_score, blur_msg = ImageQualityChecker.check_blur(image_data)
        resolution_passed, resolution_msg = ImageQualityChecker.check_resolution(image_data)
        brightness_passed, brightness_msg = ImageQualityChecker.check_brightness(image_data)
        
        is_valid = blur_passed and resolution_passed and brightness_passed
        
        if is_valid:
            overall_msg = "Image quality is acceptable for processing."
        else:
            issues = []
            if not blur_passed:
                issues.append("too blurry")
            if not resolution_passed:
                issues.append("too small")
            if not brightness_passed:
                issues.append("lighting issues")
            overall_msg = f"Image quality issues detected: {', '.join(issues)}. Please upload a clearer, well-lit photo."
        
        return {
            "is_valid": is_valid,
            "blur_check": {
                "passed": blur_passed,
                "score": blur_score,
                "message": blur_msg
            },
            "resolution_check": {
                "passed": resolution_passed,
                "message": resolution_msg
            },
            "brightness_check": {
                "passed": brightness_passed,
                "message": brightness_msg
            },
            "overall_message": overall_msg
        }

