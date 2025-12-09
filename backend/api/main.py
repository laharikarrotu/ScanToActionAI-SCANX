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
import hashlib

class Settings(BaseSettings):
    frontend_url: str = "http://localhost:3000"
    allowed_domains: str = ""
    openai_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()

app = FastAPI(
    title="SCANX API",
    description="Vision-grounded AI agent backend",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
vision_engine = VisionEngine(api_key=settings.openai_api_key)
planner_engine = PlannerEngine(api_key=settings.openai_api_key)
event_logger = EventLogger()

@app.get("/")
async def root():
    return {"message": "SCANX API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

class AnalyzeRequest(BaseModel):
    intent: str
    context: Optional[dict] = None

@app.post("/analyze-and-execute")
async def analyze_and_execute(
    file: UploadFile = File(...),
    intent: str = Form(...),
    context: Optional[str] = Form(None)
):
    """
    Main endpoint: Takes image + intent, analyzes, plans, and executes
    """
    try:
        # Read image
        image_data = await file.read()
        image_hash = hashlib.md5(image_data).hexdigest()
        
        # Log request
        event_logger.log_scan_request(image_hash, intent)
        
        # Step 1: Vision - Understand UI
        ui_schema = vision_engine.analyze_image(image_data)
        ui_schema_dict = ui_schema.model_dump()
        event_logger.log_ui_schema(ui_schema_dict)
        
        if not ui_schema.elements:
            raise HTTPException(status_code=400, detail="Could not detect UI elements")
        
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
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
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

