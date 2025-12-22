#!/usr/bin/env python3
"""
Test backend module imports and configuration
"""
from api.config import settings

print('🔍 Testing Backend Configuration...')
openai_set = 'SET' if settings.openai_api_key and settings.openai_api_key != 'your_key_here' else 'NOT SET'
print(f'✅ OpenAI API Key: {openai_set}')
print(f'✅ Database URL: {"SET" if settings.database_url else "NOT SET"}')
print(f'✅ Frontend URL: {settings.frontend_url}')
print(f'✅ JWT Secret: {"SET" if settings.jwt_secret else "NOT SET"}')

# Check if backend can import all modules
try:
    from api.main import app
    print('✅ FastAPI app imports successfully')
    
    from vision.ui_detector import VisionEngine
    print('✅ Vision engine imports successfully')
    
    from planner.agent_planner import PlannerEngine
    print('✅ Planner engine imports successfully')
    
    from executor.browser_executor import BrowserExecutor
    print('✅ Executor engine imports successfully')
    
    from medication.prescription_extractor import PrescriptionExtractor
    print('✅ Prescription extractor imports successfully')
    
    from medication.interaction_checker import InteractionChecker
    print('✅ Interaction checker imports successfully')
    
    from nutrition.diet_advisor import DietAdvisor
    print('✅ Diet advisor imports successfully')
    
    print('✅ All backend modules loaded successfully!')
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

