"""
Authentication endpoints (legacy JWT login)
"""
from fastapi import APIRouter, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import re

from api.config import settings
from api.auth import create_access_token, verify_token
from api.oauth_auth import get_current_user as get_oauth_user
from api.rate_limiter import RateLimiter
from core.logger import get_logger

logger = get_logger("api.routers.auth")
router = APIRouter(prefix="", tags=["authentication"])

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Login endpoint for authentication.
    
    **Security Features:**
    - Rate limiting on login attempts
    - Input validation and sanitization
    - Password validation (basic - replace with database check in production)
    
    **Parameters**:
    - `username`: User identifier (max 100 chars, alphanumeric + underscore only)
    - `password`: User password (min 8 chars, max 128 chars)
    
    **Returns**:
    - JWT access token for authenticated requests
    """
    # Rate limiting for login attempts (stricter than general API)
    client_ip = request.client.host if request.client else "unknown"
    login_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)
    allowed, remaining = login_rate_limiter.is_allowed(f"login:{client_ip}")
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Please try again in {remaining} seconds."
        )
    
    # Input validation and sanitization
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="Username is required")
    
    if not password or not password.strip():
        raise HTTPException(status_code=400, detail="Password is required")
    
    # Sanitize username (alphanumeric + underscore, max 100 chars)
    username = username.strip()[:100]
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise HTTPException(status_code=400, detail="Username contains invalid characters")
    
    # Validate password length
    password = password.strip()
    if len(password) < 8 or len(password) > 128:
        raise HTTPException(status_code=400, detail="Password must be between 8 and 128 characters")
    
    # Note: This is a demo implementation. For production:
    # - Validate credentials against database
    # - Hash passwords with bcrypt
    # - Implement account lockout after failed attempts
    logger.info(f"Login attempt for user: {username}", context={"endpoint": "login", "ip": client_ip})
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/protected")
async def protected_route(current_user: dict = Depends(verify_token)):
    """Example protected route requiring JWT auth (legacy)"""
    return {"message": f"Hello {current_user.get('sub')}, you are authenticated"}

@router.get("/protected-oauth")
async def protected_oauth_route(current_user: dict = Depends(get_oauth_user)):
    """Example protected route requiring OAuth (Auth0 or Google)"""
    return {
        "message": f"Hello {current_user.get('name', current_user.get('sub'))}, you are authenticated via {current_user.get('auth_provider', 'unknown')}",
        "user": {
            "id": current_user.get("sub"),
            "email": current_user.get("email"),
            "name": current_user.get("name"),
            "picture": current_user.get("picture")
        }
    }

