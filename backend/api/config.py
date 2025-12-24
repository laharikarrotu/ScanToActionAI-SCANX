"""
Configuration settings for the API
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
import secrets

class Settings(BaseSettings):
    frontend_url: str = "http://localhost:3000"
    allowed_domains: str = ""
    # OpenAI removed - using Gemini only
    # openai_api_key: Optional[str] = None  # REMOVED
    # anthropic_api_key: Optional[str] = None  # REMOVED
    gemini_api_key: str  # REQUIRED - No default, must be set in .env
    database_url: Optional[str] = None
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    # Security and validation constants
    max_file_size_mb: int = 10  # Maximum file size in MB
    max_file_count: int = 10  # Maximum number of files per request
    max_intent_length: int = 500  # Maximum intent string length
    max_json_size_kb: int = 100  # Maximum JSON payload size in KB
    cache_ttl_hours: int = 24  # Cache TTL in hours
    ui_schema_cache_ttl_seconds: int = 3600  # UI schema cache TTL in seconds
    
    # OAuth Authentication (Auth0 or Google)
    # Option 1: Auth0 (Recommended for production)
    auth0_domain: Optional[str] = None  # e.g., "your-tenant.auth0.com"
    auth0_audience: Optional[str] = None  # Your API identifier from Auth0
    auth0_client_id: Optional[str] = None  # Auth0 Application Client ID
    auth0_client_secret: Optional[str] = None  # Auth0 Application Client Secret
    
    # Option 2: Direct Google OAuth (Simpler, free)
    google_client_id: Optional[str] = None  # Google OAuth Client ID
    google_client_secret: Optional[str] = None  # Google OAuth Client Secret (for backend)
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env that aren't in this class

settings = Settings()

# Security: Validate JWT secret is not default value
DEFAULT_JWT_SECRET = "change-me-in-production"
if settings.jwt_secret == DEFAULT_JWT_SECRET:
    # In production, fail immediately
    if os.getenv("NODE_ENV") == "production" or os.getenv("ENVIRONMENT") == "production":
        raise ValueError(
            "CRITICAL SECURITY ERROR: JWT_SECRET is set to default value 'change-me-in-production'. "
            "This is not allowed in production. Please set a strong, random JWT_SECRET in your .env file."
        )
    else:
        # In development, generate a random secret and warn
        import warnings
        warnings.warn(
            f"⚠️  SECURITY WARNING: JWT_SECRET is set to default value. "
            f"Generated random secret for this session only. "
            f"Set JWT_SECRET in .env file for production use.",
            UserWarning
        )
        # Generate a temporary random secret (not persisted)
        settings.jwt_secret = secrets.token_urlsafe(32)

