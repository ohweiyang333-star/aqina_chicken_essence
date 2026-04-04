"""Core configuration for Aqina Backend."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Firebase
    firebase_project_id: str = "aqina-chicken-essence"
    firebase_storage_bucket: str = "aqina-chicken-essence.firebasestorage.app"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://aqina-frontend-*.a.run.app",
    ]

    # JWT (optional, for session tokens)
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 86400  # 24 hours in seconds

    # Environment
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
