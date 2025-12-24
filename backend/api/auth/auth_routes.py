"""
OAuth authentication routes for Google Sign-In and Auth0
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from api.config import settings
from .oauth_auth import get_current_user, verify_oauth_token
from .auth import create_access_token
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
    Handles both Auth0 and Google OAuth callbacks
    """
    if error:
        logger.warning(f"OAuth error: {error}")
        return JSONResponse(
            status_code=400,
            content={"error": "OAuth authentication failed", "details": error}
        )
    
    if not code:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing authorization code"}
        )
    
    # Exchange code for token (implementation depends on provider)
    # This is a simplified version - full implementation would exchange code
    try:
        # Verify the token from the OAuth provider
        # In a real implementation, you'd exchange the code for a token here
        user_info = verify_oauth_token(code)
        
        # Create JWT token for our API
        access_token = create_access_token(data={"sub": user_info.get("sub", "user")})
        
        return JSONResponse(content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_info
        })
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to process OAuth callback"}
        )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Logged out successfully"}

