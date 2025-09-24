"""User model for authentication and project ownership."""

from typing import Optional, List
from datetime import datetime
from pydantic import Field, EmailStr, validator
from app.models.base import BaseDocument, PyObjectId


class User(BaseDocument):
    """User model for authentication."""

    username: str = Field(..., min_length=3, max_length=50, unique=True)
    email: EmailStr = Field(..., unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    project_ids: List[PyObjectId] = Field(default_factory=list)
    last_login: Optional[datetime] = None

    @validator('username')
    def validate_username(cls, v):
        """Ensure username is alphanumeric with underscores only."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric with underscores only')
        return v

    class Config:
        collection_name = "users"
        indexes = [
            {"fields": ["username"], "unique": True},
            {"fields": ["email"], "unique": True}
        ]