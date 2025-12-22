"""
OAuth authentication routes for Google Sign-In and Auth0
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from api.config import settings
from api.oauth_auth import get_current_user, verify_oauth_token
from api.auth import create_access_token
from core.logger import get_logger

logger = get_logger("api.auth_routes")
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: Optional[str] = None,
    error: Optional[str] = None
):
    """
    OAuth callback endpoint
    This is called by Auth0/Google after user authentication
    """
    if error:
        logger.warning(f"OAuth error: {error}")
        return JSONResponse(
            status_code=400,
            content={"error": "Authentication failed", "detail": error}
        )
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    # In a real implementation, you would:
    # 1. Exchange the code for tokens
    # 2. Get user info from the provider
    # 3. Create or update user in your database
    # 4. Generate your own JWT token
    
    # For now, return instructions
    return JSONResponse(
        content={
            "message": "OAuth callback received",
            "note": "Frontend should handle token exchange. See documentation."
        }
    )

@router.get("/me")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    Requires valid OAuth token (Auth0 or Google)
    """
    return {
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "picture": current_user.get("picture"),
        "auth_provider": current_user.get("auth_provider", "unknown"),
        "email_verified": current_user.get("email_verified", False)
    }

@router.post("/token")
async def exchange_token(
    request: Request,
    id_token: str
):
    """
    Exchange OAuth ID token for your own JWT token
    This allows you to issue your own tokens after OAuth verification
    """
    from fastapi.security import HTTPAuthorizationCredentials
    
    try:
        # Create a mock credentials object for verification
        class MockCredentials:
            def __init__(self, token: str):
                self.credentials = token
        
        # Verify the OAuth token
        user_info = await verify_oauth_token(MockCredentials(id_token))
        
        # Create your own JWT token
        access_token = create_access_token(
            data={
                "sub": user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "auth_provider": user_info.get("auth_provider", "unknown")
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture")
            }
        }
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

