"""
Configuration settings for the API
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    frontend_url: str = "http://localhost:3000"
    allowed_domains: str = ""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    database_url: Optional[str] = None
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env that aren't in this class

settings = Settings()

