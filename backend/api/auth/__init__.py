"""
Authentication Module
Provides JWT and OAuth authentication utilities
"""
from .auth import create_access_token, verify_token, get_current_user
from .oauth_auth import (
    get_current_user as get_oauth_user,
    verify_oauth_token,
    Auth0Verifier,
    GoogleOAuthVerifier
)
from .auth_routes import router as auth_router

__all__ = [
    "create_access_token",
    "verify_token",
    "get_current_user",
    "get_oauth_user",
    "verify_oauth_token",
    "Auth0Verifier",
    "GoogleOAuthVerifier",
    "auth_router",
]

