from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision.ui_detector import VisionEngine, UISchema
from vision.image_quality import ImageQualityChecker
from planner.agent_planner import PlannerEngine, ActionPlan
from executor.browser_executor import BrowserExecutor, ExecutionResult
from memory.event_log import EventLogger
from api.config import settings
from api.auth import create_access_token, verify_token
from medication.prescription_extractor import PrescriptionExtractor
from medication.interaction_checker import InteractionChecker, Medication
from nutrition.diet_advisor import DietAdvisor
from nutrition.condition_advisor import ConditionAdvisor
from nutrition.food_scanner import FoodScanner
from fastapi import Depends
from api.rate_limiter import RateLimiter
from fastapi import Request
import hashlib

# Optional scalability modules (graceful fallback if not available)
try:
    from core.rate_limiter_redis import RedisRateLimiter
    REDIS_RATE_LIMITER_AVAILABLE = True
except ImportError:
    REDIS_RATE_LIMITER_AVAILABLE = False
    RedisRateLimiter = None

# Free rate limiting alternatives
try:
    from core.rate_limiter_db import DatabaseRateLimiter
    DATABASE_RATE_LIMITER_AVAILABLE = True
except ImportError:
    DATABASE_RATE_LIMITER_AVAILABLE = False
    DatabaseRateLimiter = None

try:
    from core.rate_limiter_token_bucket import TokenBucketRateLimiter
    TOKEN_BUCKET_AVAILABLE = True
except ImportError:
    TOKEN_BUCKET_AVAILABLE = False
    TokenBucketRateLimiter = None

try:
    from core.cache import cache_manager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    cache_manager = None

try:
    from core.circuit_breaker import openai_circuit_breaker
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    # Create a simple pass-through wrapper
    class SimpleCircuitBreaker:
        def call(self, func, *args, **kwargs):
            return func(*args, **kwargs)
        async def call_async(self, func, *args, **kwargs):
            return await func(*args, **kwargs)
    openai_circuit_breaker = SimpleCircuitBreaker()

# Remove unused imports - retry_with_backoff and task_queue not used
# They're available in core/ but not needed in main.py

# Parse allowed origins (comma-separated or single URL)
allowed_origins = [url.strip() for url in settings.frontend_url.split(",")]
allowed_origins.append("http://localhost:3000")  # Always allow localhost for dev
# Allow Expo Go and mobile apps
allowed_origins.extend([
    "exp://192.168.1.97:8081",  # Expo dev server
    "exp://localhost:8081",
])
allowed_origins = list(set(allowed_origins))  # Remove duplicates

app = FastAPI(
    title="HealthScan API",
    description="AI healthcare assistant backend - helps with medical forms, prescriptions, and healthcare paperwork",
    version="0.1.0"
)

# CORS - supports multiple origins (localhost + Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines - Use Gemini if available, otherwise OpenAI
try:
    if settings.gemini_api_key:
        from vision.gemini_detector import GeminiVisionEngine
        from planner.gemini_planner import GeminiPlannerEngine
        vision_engine = GeminiVisionEngine(api_key=settings.gemini_api_key)
        planner_engine = GeminiPlannerEngine(api_key=settings.gemini_api_key)
        print("✅ Using Gemini Pro 1.5 for Vision and Planning")
    else:
        vision_engine = VisionEngine(api_key=settings.openai_api_key)
        planner_engine = PlannerEngine(api_key=settings.openai_api_key)
        print("✅ Using OpenAI GPT-4o for Vision and Planning")
except Exception as e:
    print(f"⚠️  Gemini setup failed: {e}, using OpenAI")
    vision_engine = VisionEngine(api_key=settings.openai_api_key)
    planner_engine = PlannerEngine(api_key=settings.openai_api_key)
event_logger = EventLogger()
prescription_extractor = PrescriptionExtractor(api_key=settings.openai_api_key)
interaction_checker = InteractionChecker()
diet_advisor = DietAdvisor(api_key=settings.openai_api_key, use_gemini=bool(settings.gemini_api_key))

# Rate limiter selection (priority: Redis > Database > Token Bucket > In-Memory)
if REDIS_RATE_LIMITER_AVAILABLE and RedisRateLimiter:
    try:
        rate_limiter = RedisRateLimiter()
        print("✅ Using Redis rate limiter")
    except Exception as e:
        print(f"Redis rate limiter failed: {e}, trying database...")
        rate_limiter = None
else:
    rate_limiter = None

if not rate_limiter and DATABASE_RATE_LIMITER_AVAILABLE and DatabaseRateLimiter and settings.database_url:
    try:
        rate_limiter = DatabaseRateLimiter()
        print("✅ Using Database rate limiter (free, multi-instance)")
    except Exception as e:
        print(f"Database rate limiter failed: {e}, trying token bucket...")
        rate_limiter = None

if not rate_limiter and TOKEN_BUCKET_AVAILABLE and TokenBucketRateLimiter:
    try:
        rate_limiter = TokenBucketRateLimiter()
        print("✅ Using Token Bucket rate limiter (free, better algorithm)")
    except Exception as e:
        print(f"Token bucket rate limiter failed: {e}, using in-memory...")
        rate_limiter = None

if not rate_limiter:
    rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
    print("✅ Using in-memory rate limiter (free, single instance)")

condition_advisor = ConditionAdvisor()
food_scanner = FoodScanner(api_key=settings.openai_api_key, use_gemini=bool(settings.gemini_api_key))

@app.get("/")
async def root():
    return {"message": "SCANX API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Optional: Simple login endpoint (for demo - replace with real auth later)
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """
    Simple login - replace with real user validation
    For now, accepts any username/password for demo
    """
    # TODO: Add real user validation against database
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}

# Example protected route
@app.get("/protected")
async def protected_route(current_user: dict = Depends(verify_token)):
    """Example protected route requiring JWT auth"""
    return {"message": f"Hello {current_user.get('sub')}, you are authenticated"}

class AnalyzeRequest(BaseModel):
    intent: str
    context: Optional[dict] = None

@app.post("/analyze-and-execute")
async def analyze_and_execute(
    request: Request,
    file: UploadFile = File(...),
    intent: str = Form(...),
    context: Optional[str] = Form(None)
):
    """
    Main endpoint: Takes image + intent, analyzes, plans, and executes
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    allowed, remaining = rate_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please try again in a moment. ({remaining} requests remaining)"
        )
    
    try:
        # Validate input
        if not intent or not intent.strip():
            raise HTTPException(status_code=400, detail="Intent is required")
        
        if len(intent) > 500:
            raise HTTPException(status_code=400, detail="Intent is too long (max 500 characters)")
        
        # Read and validate image
        image_data = await file.read()
        
        # Check file size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image is too large (max 10MB)")
        
        # Check file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check image quality (blur, resolution, brightness)
        quality_checker = ImageQualityChecker()
        quality_result = quality_checker.validate_image(image_data)
        
        if not quality_result["is_valid"]:
            # Image is too blurry or has quality issues
            error_message = quality_result["overall_message"]
            raise HTTPException(
                status_code=400, 
                detail=error_message
            )
        
        image_hash = hashlib.md5(image_data).hexdigest()
        
        # Check cache first (if available)
        if CACHE_AVAILABLE and cache_manager:
            cached_result = cache_manager.get_ui_schema(image_hash, intent)
            if cached_result:
                import logging
                logging.info(f"Cache hit for image {image_hash[:8]}...")
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "ui_schema": cached_result,
                        "cached": True
                    }
                )
        
        # Log request
        event_logger.log_scan_request(image_hash, intent)
        
        # Step 1: Vision - Understand UI (with circuit breaker protection if available)
        try:
            # Wrap synchronous call for circuit breaker
            def analyze_image_sync():
                return vision_engine.analyze_image(image_data)
            
            # Use circuit breaker for protection (or direct call if not available)
            if CIRCUIT_BREAKER_AVAILABLE:
                ui_schema = openai_circuit_breaker.call(analyze_image_sync)
            else:
                ui_schema = analyze_image_sync()
            ui_schema_dict = ui_schema.model_dump()
            event_logger.log_ui_schema(ui_schema_dict)
            
            # Cache the result (if available)
            if CACHE_AVAILABLE and cache_manager:
                cache_manager.set_ui_schema(image_hash, intent, ui_schema_dict, ttl=3600)
            
            # Log for debugging
            import logging
            logging.info(f"Vision analysis completed: {len(ui_schema.elements)} elements found")
            
        except Exception as e:
            import logging
            logging.error(f"Vision analysis error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail=f"Vision analysis failed: {str(e)}. Please check your OpenAI API key and credits."
            )
        
        # Check if we have elements - but be more lenient
        if not ui_schema.elements or len(ui_schema.elements) == 0:
            # Even if no elements, return what we have (might have OCR fallback elements)
            if ui_schema.elements:
                # We have some elements, proceed
                pass
            else:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "no_elements",
                        "message": "Could not detect UI elements in the image. Try a clearer image or different angle.",
                        "ui_schema": ui_schema_dict,
                        "debug": "No elements extracted from image or OCR"
                    }
                )
        
        # Step 2: Planning - Create action plan
        # Parse context safely (avoid eval() for security)
        context_dict = None
        if context:
            try:
                import json
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                # If not valid JSON, ignore context
                context_dict = None
        
        plan = planner_engine.create_plan(
            user_intent=intent,
            ui_schema=ui_schema_dict,
            context=context_dict
        )
        plan_dict = plan.model_dump()
        event_logger.log_action_plan(plan_dict)
        
        # Log plan details for debugging
        import logging
        logging.info(f"Action plan created: {len(plan.steps)} steps")
        for i, step in enumerate(plan.steps):
            logging.info(f"  Step {i+1}: {step.action} on {step.target} - {step.description}")
        
        if not plan.steps:
            import logging
            logging.warning("Plan created but no steps generated. Elements available: " + str(len(ui_schema.elements)))
            return JSONResponse(
                status_code=200,
                content={
                    "status": "plan_only",
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "message": "Plan created but no steps to execute. Please try a more specific intent like 'Fill this form' or 'Extract prescription details'."
                }
            )
        
        # Step 3: Execution - Execute plan
        executor = BrowserExecutor(headless=True)
        try:
            # Get URL hint from schema or use default
            start_url = ui_schema.url_hint or "https://example.com"
            
            result = await executor.execute_plan(
                steps=plan.steps,
                ui_schema=ui_schema_dict,
                start_url=start_url
            )
            
            result_dict = result.model_dump()
            event_logger.log_execution_result(result_dict)
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": result.status,
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "execution": result_dict,
                    "message": result.message
                }
            )
        finally:
            await executor.close()
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # Log the full error for debugging
        import logging
        logging.error(f"Error in analyze-and-execute: {error_msg}", exc_info=True)
        event_logger.log_event("error", {"error": error_msg, "endpoint": "analyze-and-execute"})
        
        # Return more detailed error for debugging (in development)
        # In production, you might want to hide some details
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": error_msg if "API key" in error_msg or "blurry" in error_msg.lower() or "quality" in error_msg.lower() else f"An error occurred: {error_msg}",
                "error_type": type(e).__name__
            }
        )

# Removed /analyze endpoint - not used by frontend
# Frontend only uses /analyze-and-execute

@app.post("/check-prescription-interactions")
async def check_prescription_interactions(
    files: List[UploadFile] = File(...),
    allergies: Optional[str] = Form(None)
):
    """
    UNIQUE FEATURE: Multi-prescription drug interaction checker
    
    Scans multiple prescription images and checks for:
    - Drug-drug interactions
    - Allergy conflicts
    - Dosage concerns
    
    This is HealthScan's unique differentiator!
    """
    try:
        import asyncio
        
        # Extract medication info from all prescriptions
        medications = []
        prescription_details = []
        
        for file in files:
            image_data = await file.read()
            prescription = prescription_extractor.extract_from_image(image_data)
            prescription_details.append(prescription.model_dump())
            
            # Convert to Medication object for interaction checking
            medications.append(Medication(
                name=prescription.medication_name,
                dosage=prescription.dosage,
                frequency=prescription.frequency
            ))
        
        # Parse allergies if provided
        allergy_list = []
        if allergies:
            allergy_list = [a.strip() for a in allergies.split(",")]
        
        # Check for interactions
        warnings = await interaction_checker.check_interactions(
            medications=medications,
            allergies=allergy_list if allergy_list else None
        )
        
        # Organize warnings by severity
        major_warnings = [w for w in warnings if w.severity == "major"]
        moderate_warnings = [w for w in warnings if w.severity == "moderate"]
        minor_warnings = [w for w in warnings if w.severity == "minor"]
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "prescriptions": prescription_details,
                "medications_found": len(medications),
                "interactions": {
                    "total": len(warnings),
                    "major": [w.model_dump() for w in major_warnings],
                    "moderate": [w.model_dump() for w in moderate_warnings],
                    "minor": [w.model_dump() for w in minor_warnings]
                },
                "has_interactions": len(warnings) > 0,
                "message": f"Found {len(warnings)} potential interaction(s)" if warnings else "No interactions detected"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.post("/get-diet-recommendations")
async def get_diet_recommendations(
    condition: str = Form(...),
    medications: Optional[str] = Form(None),
    dietary_restrictions: Optional[str] = Form(None)
):
    """
    Get diet recommendations based on medical condition
    Used by DietPortal component
    """
    try:
        med_list = [m.strip() for m in medications.split(",")] if medications else None
        restrictions_list = [r.strip() for r in dietary_restrictions.split(",")] if dietary_restrictions else None
        
        recommendation = diet_advisor.get_diet_recommendations(
            condition=condition,
            medications=med_list,
            dietary_restrictions=restrictions_list
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "recommendations": recommendation.model_dump()
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.post("/check-food-compatibility")
async def check_food_compatibility(
    food_item: str = Form(...),
    condition: Optional[str] = Form(None),
    medications: Optional[str] = Form(None)
):
    """
    Check if a food item is compatible with condition/medications
    Used by DietPortal component
    """
    try:
        med_list = [m.strip() for m in medications.split(",")] if medications else None
        
        compatibility = diet_advisor.check_food_compatibility(
            food_item=food_item,
            condition=condition,
            medications=med_list
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "compatibility": compatibility
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.post("/generate-meal-plan")
async def generate_meal_plan(
    condition: str = Form(...),
    days: int = Form(7),
    dietary_restrictions: Optional[str] = Form(None)
):
    """
    Generate a meal plan for a medical condition
    Used by DietPortal component
    """
    try:
        restrictions_list = [r.strip() for r in dietary_restrictions.split(",")] if dietary_restrictions else None
        
        meal_plan = diet_advisor.generate_meal_plan(
            condition=condition,
            days=days,
            dietary_restrictions=restrictions_list
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "meal_plan": meal_plan
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

