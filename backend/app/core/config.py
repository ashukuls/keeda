"""Application configuration."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, computed_field


class Settings(BaseSettings):
    """Application settings."""

    # Application
    PROJECT_NAME: str = "Keeda"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # MongoDB Components
    MONGO_HOST: str = Field(default="localhost")
    MONGO_PORT: int = Field(default=27017)
    MONGO_USERNAME: Optional[str] = Field(default=None)
    MONGO_PASSWORD: Optional[str] = Field(default=None)
    MONGO_AUTH_SOURCE: str = Field(default="admin")
    DATABASE_NAME: str = Field(default="keeda")

    # MongoDB Admin (for scripts)
    MONGO_ADMIN_USERNAME: Optional[str] = Field(default=None)
    MONGO_ADMIN_PASSWORD: Optional[str] = Field(default=None)

    # Test Database
    TEST_DATABASE_NAME: str = Field(default="keeda_test")

    @computed_field
    @property
    def MONGODB_URL(self) -> str:
        """Build MongoDB URL from components."""
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.DATABASE_NAME}?authSource={self.MONGO_AUTH_SOURCE}"
        return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/{self.DATABASE_NAME}"

    @computed_field
    @property
    def TEST_MONGODB_URL(self) -> str:
        """Build test MongoDB URL from components."""
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.TEST_DATABASE_NAME}?authSource={self.MONGO_AUTH_SOURCE}"
        return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/{self.TEST_DATABASE_NAME}"

    @computed_field
    @property
    def MONGO_ADMIN_URL(self) -> str:
        """Build admin MongoDB URL for scripts."""
        if self.MONGO_ADMIN_USERNAME and self.MONGO_ADMIN_PASSWORD:
            return f"mongodb://{self.MONGO_ADMIN_USERNAME}:{self.MONGO_ADMIN_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/?authSource={self.MONGO_AUTH_SOURCE}"
        return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/"

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

    # Ollama Configuration
    OLLAMA_BASE_URL: Optional[str] = Field(default="http://localhost:11434")
    OLLAMA_MODEL: Optional[str] = Field(default="llama3.2")

    # Local Image Generation
    IMAGE_API_BASE_URL: Optional[str] = Field(default="http://localhost:7860")
    IMAGE_API_TYPE: Optional[str] = Field(default="automatic1111")

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