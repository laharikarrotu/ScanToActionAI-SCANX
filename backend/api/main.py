from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
import json
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision.ui_detector import VisionEngine, UISchema
from vision.image_quality import ImageQualityChecker
from planner.agent_planner import PlannerEngine, ActionPlan
from executor.browser_executor import BrowserExecutor, ExecutionResult
from memory.event_log import EventLogger
from core.error_handler import ErrorHandler, handle_errors
from core.resource_manager import ResourceManager
from core.encryption import ImageEncryption
from core.audit_logger import AuditLogger, AuditAction
from core.streaming import StreamingResponseBuilder
from core.logger import get_logger
from core.middleware import RequestLoggingMiddleware, PerformanceMiddleware
from api.config import settings
from api.auth import create_access_token, verify_token
from medication.prescription_extractor import PrescriptionExtractor, PrescriptionInfo
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
    description="""
    AI healthcare assistant backend for medical document processing.
    
    ## Features
    
    * **Prescription Extraction**: Extract medication details from prescription images
    * **Drug Interaction Checking**: Check for drug-drug and drug-allergy interactions
    * **Diet Recommendations**: Get personalized diet recommendations based on medical conditions
    * **Form Automation**: Automate medical form filling using AI vision and browser automation
    
    ## Authentication
    
    Most endpoints require JWT authentication. Get a token via `/login`.
    
    ## HIPAA Compliance
    
    ⚠️ **Important**: This is an MVP and is NOT HIPAA-compliant for production use with real patient data.
    See documentation for compliance roadmap.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - supports multiple origins (localhost + Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging and performance tracking middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(PerformanceMiddleware)

# Initialize engines - Use combined analyzer if Gemini available, otherwise separate engines
USE_COMBINED_ANALYZER = False
combined_analyzer = None
vision_engine = None
planner_engine = None

try:
    if settings.gemini_api_key:
        # Try combined analyzer first (1 API call instead of 2) - OPTIMIZATION!
        try:
            from vision.combined_analyzer import CombinedAnalyzer
            combined_analyzer = CombinedAnalyzer(api_key=settings.gemini_api_key)
            USE_COMBINED_ANALYZER = True
            logger.info("Using Combined Analyzer (Vision + Planning in 1 call) - 50% faster & cheaper!")
        except Exception as e:
            logger.warning(f"Combined analyzer failed: {e}, using separate engines", exception=e)
            USE_COMBINED_ANALYZER = False
            from vision.gemini_detector import GeminiVisionEngine
            from planner.gemini_planner import GeminiPlannerEngine
            vision_engine = GeminiVisionEngine(api_key=settings.gemini_api_key)
            planner_engine = GeminiPlannerEngine(api_key=settings.gemini_api_key)
            logger.info("Using Gemini Pro 1.5 for Vision and Planning (separate calls)")
    else:
        USE_COMBINED_ANALYZER = False
        vision_engine = VisionEngine(api_key=settings.openai_api_key)
        planner_engine = PlannerEngine(api_key=settings.openai_api_key)
        logger.info("Using OpenAI GPT-4o for Vision and Planning")
except Exception as e:
    logger.warning(f"Gemini setup failed: {e}, using OpenAI", exception=e)
    USE_COMBINED_ANALYZER = False
    vision_engine = VisionEngine(api_key=settings.openai_api_key)
    planner_engine = PlannerEngine(api_key=settings.openai_api_key)

# Initialize logging
logger = get_logger("api.main")

event_logger = EventLogger()
error_handler = ErrorHandler(max_retries=3, retry_delay=1.0)
resource_manager = ResourceManager(default_timeout=30.0)
# HIPAA Compliance: Image encryption and audit logging
image_encryption = ImageEncryption()
audit_logger = AuditLogger()

logger.info("Initializing HealthScan API", context={"version": "1.0.0"})
prescription_extractor = PrescriptionExtractor(api_key=settings.openai_api_key)
interaction_checker = InteractionChecker()
# Force Gemini for diet advisor if available (cheaper and avoids OpenAI quota issues)
diet_advisor = DietAdvisor(api_key=settings.openai_api_key, use_gemini=bool(settings.gemini_api_key))
if settings.gemini_api_key:
    logger.info("Diet Advisor using Gemini Pro 1.5 (cheaper & avoids quota issues)")
else:
    logger.warning("Diet Advisor using OpenAI (Gemini API key not set)")

# Rate limiter selection (priority: Redis > Database > Token Bucket > In-Memory)
if REDIS_RATE_LIMITER_AVAILABLE and RedisRateLimiter:
    try:
        rate_limiter = RedisRateLimiter()
        logger.info("Using Redis rate limiter")
    except Exception as e:
        logger.warning(f"Redis rate limiter failed: {e}, trying database...", exception=e)
        rate_limiter = None
else:
    rate_limiter = None

if not rate_limiter and DATABASE_RATE_LIMITER_AVAILABLE and DatabaseRateLimiter and settings.database_url:
    try:
        rate_limiter = DatabaseRateLimiter()
        logger.info("Using Database rate limiter (free, multi-instance)")
    except Exception as e:
        logger.warning(f"Database rate limiter failed: {e}, trying token bucket...", exception=e)
        rate_limiter = None

if not rate_limiter and TOKEN_BUCKET_AVAILABLE and TokenBucketRateLimiter:
    try:
        rate_limiter = TokenBucketRateLimiter()
        logger.info("Using Token Bucket rate limiter (free, better algorithm)")
    except Exception as e:
        logger.warning(f"Token bucket rate limiter failed: {e}, using in-memory...", exception=e)
        rate_limiter = None

if not rate_limiter:
    rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
    logger.info("Using in-memory rate limiter (free, single instance)")

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
    Simple login endpoint for authentication.
    
    **Note**: This is a demo implementation. For production:
    - Validate credentials against database
    - Implement password hashing (bcrypt)
    - Add rate limiting for login attempts
    - Implement account lockout after failed attempts
    
    **Parameters**:
    - `username`: User identifier
    - `password`: User password (currently not validated)
    
    **Returns**:
    - JWT access token for authenticated requests
    """
    # Demo implementation - accepts any credentials
    # Production: Validate against database, hash passwords, rate limit
    logger.info(f"Login attempt for user: {username}", context={"endpoint": "login"})
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

@app.post("/extract-prescription")
async def extract_prescription_direct(
    request: Request,
    file: UploadFile = File(...),
    stream: bool = Form(False)  # Optional: enable streaming
):
    """
    FAST DIRECT ENDPOINT: Extract prescription data immediately.
    
    Like ChatGPT - just scan and get medications directly.
    No vision/planner steps, just pure extraction.
    
    **Parameters:**
    - `file`: Image file (prescription, medical form, etc.)
    - `stream`: Enable Server-Sent Events (SSE) for real-time progress updates
    
    **Returns:**
    - `prescription_info`: Extracted medication details (name, dosage, frequency, etc.)
    - `cached`: Whether result was served from cache
    
    **HIPAA Compliance:**
    - All image uploads are logged for audit
    - Images can be encrypted at rest (configurable)
    """
    try:
        # Read image
        image_data = await file.read()
        
        # HIPAA Compliance: Log image upload
        client_ip = request.client.host if request.client else "unknown"
        image_hash = hashlib.md5(image_data).hexdigest()
        audit_logger.log_image_upload(user_id=None, image_hash=image_hash, ip_address=client_ip)
        
        # HIPAA Compliance: Encrypt image at rest (if storing)
        # Note: For in-memory processing, encryption happens if we store the image
        # Currently processing in memory, but encryption ready for storage use
        # To enable storage encryption, uncomment:
        # encrypted_image = image_encryption.encrypt_image(image_data)
        # Store encrypted_image in database/storage instead of raw image_data
        
        # Check cache first (if available)
        if CACHE_AVAILABLE and cache_manager:
            cached_prescription = cache_manager.get_prescription(image_hash)
            if cached_prescription:
                logger.info(f"Cache hit for prescription {image_hash[:8]}...", context={"cache": "hit", "image_hash": image_hash[:8]})
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "cached": True,
                        "prescription_info": cached_prescription,
                        "message": "Prescription extracted successfully (cached)"
                    }
                )
        
        # Direct extraction using prescription extractor
        prescription = prescription_extractor.extract_from_image(image_data)
        prescription_dict = prescription.model_dump()
        
        # HIPAA Compliance: Log prescription extraction
        audit_logger.log_prescription_extraction(
            user_id=None,
            image_hash=image_hash,
            ip_address=client_ip
        )
        
        # Cache the result (if available)
        if CACHE_AVAILABLE and cache_manager:
            cache_manager.set_prescription(image_hash, prescription_dict, ttl=86400)  # 24 hours
        
        # Return structured data immediately
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "prescription_info": prescription_dict,
                "message": "Prescription extracted successfully"
            }
        )
    except Exception as e:
        ErrorHandler.log_error(e, {"endpoint": "extract-prescription"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        raise HTTPException(
            status_code=500,
            detail=user_friendly_msg
        )

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
        
        # HIPAA Compliance: Log image upload
        image_hash = hashlib.md5(image_data).hexdigest()
        audit_logger.log_image_upload(user_id=None, image_hash=image_hash, ip_address=client_ip)
        
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
        
        # Parse context safely
        context_dict = None
        if context:
            try:
                import json
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                context_dict = None
        
        # OPTIMIZATION: Use combined analyzer if available (1 API call instead of 2)
        # This saves 50% cost and time by doing vision + planning in one Gemini call
        ui_schema = None
        plan = None
        ui_schema_dict = None
        plan_dict = None
        used_combined = False
        
        if USE_COMBINED_ANALYZER and combined_analyzer:
            try:
                import logging
                logging.info("🚀 Using combined analyzer (Vision + Planning in 1 call) - 50% faster & cheaper!")
                
                # Single API call for both vision and planning
                def analyze_and_plan_sync():
                    return combined_analyzer.analyze_and_plan(
                        image_data=image_data,
                        user_intent=intent,
                        context=context_dict
                    )
                
                # Use circuit breaker if available
                if CIRCUIT_BREAKER_AVAILABLE:
                    ui_schema, plan = openai_circuit_breaker.call(analyze_and_plan_sync)
                else:
                    ui_schema, plan = analyze_and_plan_sync()
                
                ui_schema_dict = ui_schema.model_dump()
                plan_dict = plan.model_dump()
                
                event_logger.log_ui_schema(ui_schema_dict)
                event_logger.log_action_plan(plan_dict)
                
                # Cache the result (if available)
                if CACHE_AVAILABLE and cache_manager:
                    cache_manager.set_ui_schema(image_hash, intent, ui_schema_dict, ttl=3600)
                
                logger.info(f"Combined analysis completed: {len(ui_schema.elements)} elements, {len(plan.steps)} steps (1 API call instead of 2)", context={"elements": len(ui_schema.elements), "steps": len(plan.steps), "optimization": "combined"})
                
                used_combined = True
                
            except Exception as e:
                import logging
                logging.error(f"Combined analyzer error: {str(e)}", exc_info=True)
                # Fallback to separate calls
                logging.info("⚠️  Falling back to separate vision + planning calls")
                used_combined = False
        
        # Fallback: Use separate vision and planning calls (if combined analyzer not available or failed)
        if not used_combined:
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
                logger.info(f"Vision analysis completed: {len(ui_schema.elements)} elements found", context={"elements_count": len(ui_schema.elements)})

            except Exception as e:
                logger.error(f"Vision analysis error: {str(e)}", exception=e, context={"endpoint": "analyze-and-execute", "step": "vision"})
                raise HTTPException(
                    status_code=500, 
                    detail=f"Vision analysis failed: {str(e)}. Please check your API key and credits."
                )
            
            # Step 2: Planning - Create action plan
            plan = planner_engine.create_plan(
                user_intent=intent,
                ui_schema=ui_schema_dict,
                context=context_dict
            )
            plan_dict = plan.model_dump()
            event_logger.log_action_plan(plan_dict)
        
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
        
        # Check if execution is needed (only for actions that require browser)
        intent_lower = intent.lower() if intent else ""
        needs_browser = any(word in intent_lower for word in ["fill", "submit", "click", "navigate", "book", "schedule", "complete form"])
        has_browser_actions = any(step.action in ["click", "fill", "select", "navigate", "submit"] for step in plan.steps)
        
        # If all steps are "read" actions, skip browser execution
        if not needs_browser and not has_browser_actions:
            # Extract data from detected elements instead
            extracted_data = {}
            for elem in ui_schema.elements:
                if elem.type in ["medication", "dosage", "prescriber", "pharmacy", "data", "text"]:
                    extracted_data[elem.id] = {
                        "type": elem.type,
                        "label": elem.label,
                        "value": elem.value or elem.label
                    }
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "extracted_data": extracted_data,
                    "message": f"Successfully extracted {len(extracted_data)} data points from the document. No browser execution needed for read-only operations."
                }
            )
        
        # Step 3: Execution - Execute plan (only if browser actions are needed)
        executor = BrowserExecutor(headless=True)
        try:
            # Get URL hint from schema or use default
            start_url = ui_schema.url_hint or "https://example.com"
            
            # Check if URL is valid (not just a placeholder)
            if start_url == "https://example.com" and not ui_schema.url_hint:
                # No real URL available - this is likely a static document
                # Extract data instead of executing
                extracted_data = {}
                structured_data = {}
                
                # Try prescription extraction
                page_type = ui_schema.page_type or ""
                if "prescription" in page_type.lower() or "medication" in intent_lower:
                    try:
                        prescription = prescription_extractor.extract_from_image(image_data)
                        if prescription and prescription.medication_name != "Unknown":
                            structured_data = {
                                "medications": [{
                                    "medication_name": prescription.medication_name,
                                    "dosage": prescription.dosage,
                                    "frequency": prescription.frequency,
                                    "quantity": prescription.quantity,
                                    "refills": prescription.refills,
                                    "instructions": prescription.instructions
                                }],
                                "prescriber": prescription.prescriber,
                                "pharmacy": prescription.pharmacy if hasattr(prescription, 'pharmacy') else None,
                                "date": prescription.date,
                                "instructions": prescription.instructions
                            }
                    except Exception as e:
                        logger.warning(f"Prescription extraction failed: {e}", exception=e, context={"endpoint": "analyze-and-execute", "step": "prescription_extraction"})
                
                # Extract from elements
                for elem in ui_schema.elements:
                    elem_type = elem.type if hasattr(elem, 'type') else elem.get("type", "")
                    elem_label = elem.label if hasattr(elem, 'label') else elem.get("label", "")
                    elem_value = elem.value if hasattr(elem, 'value') else elem.get("value", "")
                    
                    if elem_type in ["medication", "dosage", "prescriber", "pharmacy", "data", "text"]:
                        extracted_data[elem.id] = {
                            "type": elem_type,
                            "label": elem_label,
                            "value": elem_value or elem_label
                        }
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "ui_schema": ui_schema_dict,
                        "plan": plan_dict,
                        "extracted_data": extracted_data,
                        "structured_data": structured_data if structured_data else None,
                        "message": f"Document analyzed. Extracted {len(extracted_data)} data points. For form filling, please provide a URL or upload a form that can be filled online."
                    }
                )
            
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
        except Exception as exec_error:
            logger.error(f"Browser execution error: {str(exec_error)}", exception=exec_error, context={"endpoint": "analyze-and-execute", "step": "browser_execution"})
            
            # Fallback: Return extracted data even if execution fails
            extracted_data = {}
            structured_data = {}
            
            # Try prescription extraction
            page_type = ui_schema.page_type or ""
            if "prescription" in page_type.lower() or "medication" in intent_lower:
                try:
                    prescription = prescription_extractor.extract_from_image(image_data)
                    if prescription and prescription.medication_name != "Unknown":
                        structured_data = {
                            "medications": [{
                                "medication_name": prescription.medication_name,
                                "dosage": prescription.dosage,
                                "frequency": prescription.frequency,
                                "quantity": prescription.quantity,
                                "refills": prescription.refills,
                                "instructions": prescription.instructions
                            }],
                            "prescriber": prescription.prescriber,
                            "pharmacy": prescription.pharmacy if hasattr(prescription, 'pharmacy') else None,
                            "date": prescription.date,
                            "instructions": prescription.instructions
                        }
                except Exception as e:
                    logger.warning(f"Prescription extraction failed: {e}", exception=e, context={"endpoint": "check-prescription-interactions", "step": "prescription_extraction"})
            
            # Extract from elements
            for elem in ui_schema.elements:
                elem_type = elem.type if hasattr(elem, 'type') else elem.get("type", "")
                elem_label = elem.label if hasattr(elem, 'label') else elem.get("label", "")
                elem_value = elem.value if hasattr(elem, 'value') else elem.get("value", "")
                
                if elem_type in ["medication", "dosage", "prescriber", "pharmacy", "data", "text"]:
                    extracted_data[elem.id] = {
                        "type": elem_type,
                        "label": elem_label,
                        "value": elem_value or elem_label
                    }
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "partial",
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "extracted_data": extracted_data,
                    "structured_data": structured_data if structured_data else None,
                    "message": f"Browser execution failed (likely no website to interact with). Extracted {len(extracted_data)} data points from the document instead."
                }
            )
        finally:
            try:
                await executor.close()
            except:
                pass  # Ignore errors during cleanup
            
    except HTTPException:
        raise
    except Exception as e:
        # Use enhanced error handler
        ErrorHandler.log_error(e, {"endpoint": "analyze-and-execute"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        event_logger.log_event("error", {"error": str(e), "endpoint": "analyze-and-execute"})
        
        # Return user-friendly error message
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg,
                "error_type": type(e).__name__
            }
        )

# Removed /analyze endpoint - not used by frontend
# Frontend only uses /analyze-and-execute

@app.post("/check-prescription-interactions")
async def check_prescription_interactions(
    request: Request,
    files: List[UploadFile] = File(...),
    allergies: Optional[str] = Form(None)
):
    """
    UNIQUE FEATURE: Multi-prescription drug interaction checker.
    
    Scans multiple prescription images and checks for:
    - Drug-drug interactions
    - Allergy conflicts
    - Dosage concerns
    
    This is HealthScan's unique differentiator!
    
    **Parameters:**
    - `files`: List of prescription image files
    - `allergies`: Comma-separated list of known allergies (optional)
    
    **Returns:**
    - `prescriptions`: Extracted prescription details
    - `interactions`: Categorized by severity (major, moderate, minor)
    - `has_interactions`: Boolean indicating if any interactions found
    """
    try:
        import asyncio
        
        # Extract medication info from all prescriptions
        medications = []
        prescription_details = []
        medication_names = []
        
        for file in files:
            image_data = await file.read()
            image_hash = hashlib.md5(image_data).hexdigest()
            
            # Check cache for prescription extraction
            cached_prescription = None
            if CACHE_AVAILABLE and cache_manager:
                cached_prescription = cache_manager.get_prescription(image_hash)
            
            if cached_prescription:
                prescription = PrescriptionInfo(**cached_prescription)
                logger.info(f"Using cached prescription for {image_hash[:8]}...", context={"cache": "hit", "image_hash": image_hash[:8]})
            else:
                prescription = prescription_extractor.extract_from_image(image_data)
                prescription_dict = prescription.model_dump()
                # Cache prescription extraction
                if CACHE_AVAILABLE and cache_manager:
                    cache_manager.set_prescription(image_hash, prescription_dict, ttl=86400)
            
            prescription_details.append(prescription.model_dump())
            medication_names.append(prescription.medication_name)
            
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
        
        # Create hash for interaction check cache key
        medications_str = ",".join(sorted(medication_names))
        allergies_str = ",".join(sorted(allergy_list)) if allergy_list else ""
        medications_hash = hashlib.md5(medications_str.encode()).hexdigest()
        allergies_hash = hashlib.md5(allergies_str.encode()).hexdigest() if allergies_str else ""
        
        # Check cache for interaction results
        if CACHE_AVAILABLE and cache_manager:
            cached_interactions = cache_manager.get_interactions(medications_hash, allergies_hash)
            if cached_interactions:
                logger.info(f"Cache hit for interactions {medications_hash[:8]}...", context={"cache": "hit", "medications_hash": medications_hash[:8]})
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "cached": True,
                        "prescription_details": prescription_details,
                        "warnings": cached_interactions.get("warnings", {}),
                        "message": f"Found interactions (cached). {cached_interactions.get('message', '')}"
                    }
                )
        
        # HIPAA Compliance: Log interaction check (accessing PHI)
        client_ip = request.client.host if request.client else "unknown"
        audit_logger.log_data_access(
            user_id=None,
            resource_type="prescription_interactions",
            resource_id=",".join(medication_names),
            ip_address=client_ip
        )
        
        # Check for interactions
        warnings = await interaction_checker.check_interactions(
            medications=medications,
            allergies=allergy_list if allergy_list else None
        )
        
        # Organize warnings by severity
        major_warnings = [w for w in warnings if w.severity == "major"]
        moderate_warnings = [w for w in warnings if w.severity == "moderate"]
        minor_warnings = [w for w in warnings if w.severity == "minor"]
        
        warnings_dict = {
            "major": [w.model_dump() for w in major_warnings],
            "moderate": [w.model_dump() for w in moderate_warnings],
            "minor": [w.model_dump() for w in minor_warnings],
        }
        
        # Cache interaction results
        if CACHE_AVAILABLE and cache_manager:
            cache_manager.set_interactions(
                medications_hash,
                allergies_hash,
                {
                    "warnings": warnings_dict,
                    "message": f"Found {len(major_warnings)} major, {len(moderate_warnings)} moderate, and {len(minor_warnings)} minor interactions."
                },
                ttl=86400  # 24 hours
            )
        
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
        ErrorHandler.log_error(e, {"endpoint": "generate-meal-plan"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg
            }
        )

@app.post("/get-diet-recommendations")
async def get_diet_recommendations(
    condition: str = Form(...),
    medications: Optional[str] = Form(None),
    dietary_restrictions: Optional[str] = Form(None)
):
    """
    Get personalized diet recommendations based on medical condition.
    
    **Parameters:**
    - `condition`: Medical condition/diagnosis (e.g., "Type 2 Diabetes")
    - `medications`: Comma-separated list of current medications (optional)
    - `dietary_restrictions`: Comma-separated dietary restrictions (optional)
    
    **Returns:**
    - `recommendations`: Foods to eat, avoid, nutritional focus, warnings
    """
    try:
        med_str = medications or ""
        diet_res_str = dietary_restrictions or ""
        
        # Check cache first
        if CACHE_AVAILABLE and cache_manager:
            cached_recommendations = cache_manager.get_diet_recommendations(condition, med_str, diet_res_str)
            if cached_recommendations:
                logger.info(f"Cache hit for diet recommendations: {condition}", context={"cache": "hit", "condition": condition})
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "recommendations": cached_recommendations,
                        "cached": True
                    }
                )
        
        med_list = [m.strip() for m in medications.split(",")] if medications else None
        restrictions_list = [r.strip() for r in dietary_restrictions.split(",")] if dietary_restrictions else None
        
        recommendation = diet_advisor.get_diet_recommendations(
            condition=condition,
            medications=med_list,
            dietary_restrictions=restrictions_list
        )
        recommendation_dict = recommendation.model_dump()
        
        # Cache the result
        if CACHE_AVAILABLE and cache_manager:
            cache_manager.set_diet_recommendations(condition, med_str, diet_res_str, recommendation_dict, ttl=86400)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "recommendations": recommendation_dict
            }
        )
    except Exception as e:
        ErrorHandler.log_error(e, {"endpoint": "get-diet-recommendations"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg
            }
        )

@app.post("/check-food-compatibility")
async def check_food_compatibility(
    food_item: str = Form(...),
    condition: Optional[str] = Form(None),
    medications: Optional[str] = Form(None)
):
    """
    Check if a food item is compatible with condition/medications.
    
    **Parameters:**
    - `food_item`: Food item to check (e.g., "Grapefruit")
    - `condition`: Medical condition (optional)
    - `medications`: Comma-separated medications (optional)
    
    **Returns:**
    - `compatibility`: Safety status, warnings, recommendations
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
        ErrorHandler.log_error(e, {"endpoint": "check-food-compatibility"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg
            }
        )

@app.post("/generate-meal-plan")
async def generate_meal_plan(
    condition: str = Form(...),
    days: int = Form(7),
    dietary_restrictions: Optional[str] = Form(None)
):
    """
    Generate a personalized meal plan for a medical condition.
    
    **Parameters:**
    - `condition`: Medical condition/diagnosis
    - `days`: Number of days for meal plan (default: 7)
    - `dietary_restrictions`: Comma-separated restrictions (optional)
    
    **Returns:**
    - `meal_plan`: Daily meal plan with breakfast, lunch, dinner, snacks
    - `shopping_list`: Ingredients needed
    - `nutritional_summary`: Calorie and nutrient breakdown
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
        ErrorHandler.log_error(e, {"endpoint": "generate-meal-plan"})
        user_friendly_msg = ErrorHandler.get_user_friendly_error(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": user_friendly_msg
            }
        )

