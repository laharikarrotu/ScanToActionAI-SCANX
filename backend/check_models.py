#!/usr/bin/env python3
"""Quick script to check available Gemini models"""
import google.generativeai as genai
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to load from backend config (uses .env file)
try:
    from api.config import settings
    api_key = settings.gemini_api_key
except Exception as e:
    # Fallback to environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print(f"ERROR: Could not load GEMINI_API_KEY from config: {e}")
        print("Please set it in .env file or as environment variable")
        exit(1)

genai.configure(api_key=api_key)

try:
    print("=== CHECKING AVAILABLE GEMINI MODELS ===\n")
    models = genai.list_models()
    available = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            name = model.name.replace('models/', '')
            available.append(name)
            print(f"✅ {name}")
    
    print(f"\n=== RECOMMENDED MODEL ===")
    if available:
        # Try common model names in order of preference
        preferred = None
        for name in ['gemini-1.5-flash-latest', 'gemini-1.5-pro-latest', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
            if name in available:
                preferred = name
                break
        if not preferred:
            preferred = available[0]
        print(f"✅ Use: '{preferred}'")
        print(f"\nAll available models: {', '.join(available)}")
    else:
        print("❌ No models found!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

