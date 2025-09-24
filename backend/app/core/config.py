"""Application configuration."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # Application
    PROJECT_NAME: str = "Keeda"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # MongoDB
    MONGODB_URL: str = Field(default="mongodb://localhost:27017")
    DATABASE_NAME: str = Field(default="keeda")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379")

    # JWT
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # AI Services
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)

    # File Storage
    IMAGE_STORAGE_PATH: str = Field(default="./data/images")
    UPLOAD_PATH: str = Field(default="./data/uploads")
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"]
    )

    # Jaeger
    JAEGER_AGENT_HOST: str = Field(default="localhost")
    JAEGER_AGENT_PORT: int = Field(default=6831)

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()