"""
HealthScan API - Main Application
Refactored to use routers for better organization
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.auth_routes import router as auth_router
from api.routers import prescription, medication, nutrition, vision, auth, monitoring, chat
from core.middleware import RequestLoggingMiddleware, PerformanceMiddleware
from core.logger import get_logger

logger = get_logger("api.main")

# Parse allowed origins (comma-separated or single URL)
allowed_origins = [url.strip() for url in settings.frontend_url.split(",")]
allowed_origins.append("http://localhost:3000")  # Always allow localhost for dev
allowed_origins.extend([
    "exp://localhost:8081",  # Expo dev server (localhost only)
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
# Security: Only allow specific methods and headers, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Add request logging and performance tracking middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(PerformanceMiddleware)

# Include all routers
app.include_router(auth_router)  # OAuth routes (/auth/*)
app.include_router(auth.router)  # Legacy auth routes (/login, /protected)
app.include_router(prescription.router)  # Prescription extraction
app.include_router(medication.router)  # Drug interactions
app.include_router(nutrition.router)  # Diet recommendations
app.include_router(vision.router)  # Vision analysis and automation
app.include_router(chat.router)  # Conversational AI chat
app.include_router(monitoring.router)  # Metrics

# Basic health endpoints
@app.get("/")
async def root():
    return {"message": "SCANX API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

logger.info("HealthScan API initialized", context={"version": "1.0.0"})

