from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision.ui_detector import VisionEngine, UISchema
from planner.agent_planner import PlannerEngine, ActionPlan
from executor.browser_executor import BrowserExecutor, ExecutionResult
from memory.event_log import EventLogger
from api.auth import create_access_token, verify_token
from medication.prescription_extractor import PrescriptionExtractor
from medication.interaction_checker import InteractionChecker, Medication
from nutrition.diet_advisor import DietAdvisor
from fastapi import Depends
from api.rate_limiter import RateLimiter
from fastapi import Request
import hashlib

class Settings(BaseSettings):
    frontend_url: str = "http://localhost:3000"
    allowed_domains: str = ""
    openai_api_key: Optional[str] = None
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    class Config:
        env_file = ".env"

settings = Settings()

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

# Initialize engines
vision_engine = VisionEngine(api_key=settings.openai_api_key)
planner_engine = PlannerEngine(api_key=settings.openai_api_key)
event_logger = EventLogger()
prescription_extractor = PrescriptionExtractor(api_key=settings.openai_api_key)
interaction_checker = InteractionChecker()
diet_advisor = DietAdvisor(api_key=settings.openai_api_key)
rate_limiter = RateLimiter(max_requests=20, window_seconds=60)  # 20 requests per minute
condition_advisor = ConditionAdvisor()
food_scanner = FoodScanner(api_key=settings.openai_api_key)

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
        
        image_hash = hashlib.md5(image_data).hexdigest()
        
        # Log request
        event_logger.log_scan_request(image_hash, intent)
        
        # Step 1: Vision - Understand UI
        try:
            ui_schema = vision_engine.analyze_image(image_data)
            ui_schema_dict = ui_schema.model_dump()
            event_logger.log_ui_schema(ui_schema_dict)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Vision analysis failed: {str(e)}. Please check your OpenAI API key and credits."
            )
        
        if not ui_schema.elements:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "no_elements",
                    "message": "Could not detect UI elements in the image. Try a clearer image or different angle.",
                    "ui_schema": ui_schema_dict
                }
            )
        
        # Step 2: Planning - Create action plan
        plan = planner_engine.create_plan(
            user_intent=intent,
            ui_schema=ui_schema_dict,
            context=eval(context) if context else None
        )
        plan_dict = plan.model_dump()
        event_logger.log_action_plan(plan_dict)
        
        if not plan.steps:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "plan_only",
                    "ui_schema": ui_schema_dict,
                    "plan": plan_dict,
                    "message": "Plan created but no steps to execute"
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
        event_logger.log_event("error", {"error": error_msg, "endpoint": "analyze-and-execute"})
        
        # Return user-friendly error
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An error occurred while processing your request. Please try again.",
                "error_type": type(e).__name__
            }
        )

@app.post("/analyze")
async def analyze_only(
    file: UploadFile = File(...),
    hint: Optional[str] = Form(None)
):
    """
    Just analyze the image, don't execute
    """
    try:
        image_data = await file.read()
        ui_schema = vision_engine.analyze_image(image_data, hint=hint)
        
        return {
            "status": "success",
            "ui_schema": ui_schema.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

