"""
Application configuration settings.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Pafar Ride Booking API"
    debug: bool = False
    environment: str = "development"
    secret_key: str = Field(..., min_length=32)
    
    # Database
    database_url: str = Field(..., description="PostgreSQL database URL")
    
    # Redis
    redis_url: str = Field(..., description="Redis connection URL")
    
    # JWT
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # External Services
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    
    # Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Firebase
    firebase_project_id: Optional[str] = None
    firebase_private_key: Optional[str] = None
    firebase_client_email: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()