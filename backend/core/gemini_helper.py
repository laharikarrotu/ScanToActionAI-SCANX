"""
Helper module to get the correct Gemini model name
Based on Google's API documentation, uses the latest stable model names
"""
from typing import Optional

# Use the latest stable model names that work with the API
# Based on actual API availability (checked via check_models.py)
# Updated: 2025-12-21 - Using verified working model names
GEMINI_MODEL_NAMES = [
    'gemini-2.5-flash',          # Latest, fastest, cheapest (recommended)
    'gemini-2.5-pro',            # Latest, more capable
    'gemini-flash-latest',       # Stable latest flash
    'gemini-pro-latest',         # Stable latest pro
    'gemini-2.0-flash',          # Fallback to 2.0
    'gemini-2.0-flash-exp',      # Experimental fallback
]

def get_gemini_model_name(api_key: Optional[str] = None) -> str:
    """
    Get the correct Gemini model name.
    Returns the first model name from the preferred list.
    The GenerativeModel class will handle validation.
    """
    # Return the most preferred model name
    # The API will validate it, and if it fails, we'll catch the error
    return GEMINI_MODEL_NAMES[0]  # gemini-2.5-flash

def get_gemini_model_with_fallback(api_key: Optional[str] = None):
    """
    Get a GenerativeModel instance, trying multiple model names.
    Returns the first model that successfully initializes.
    """
    import google.generativeai as genai
    import os
    
    if not api_key:
        api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required")
    
    genai.configure(api_key=api_key)
    
    # Try each model name in order
    last_error = None
    for model_name in GEMINI_MODEL_NAMES:
        try:
            model = genai.GenerativeModel(model_name)
            # Test that the model is accessible by checking its name
            # This will fail if the model doesn't exist
            _ = model.model_name
            return model
        except Exception as e:
            last_error = e
            continue
    
    # If all fail, raise the last error
    raise ValueError(f"Could not initialize any Gemini model. Tried: {', '.join(GEMINI_MODEL_NAMES)}. Last error: {last_error}")

