"""Project model for graphic novel projects."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import Field
from app.models.base import BaseDocument, PyObjectId


class ProjectStatus(str, Enum):
    """Project status enum."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectSettings(BaseDocument):
    """Project-specific settings."""

    default_llm_provider: str = Field(default="openai")
    default_llm_model: str = Field(default="gpt-4")
    default_image_provider: str = Field(default="dalle")
    default_image_model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1)
    image_style: Optional[str] = None
    image_size: str = Field(default="1024x1024")
    enable_auto_generation: bool = Field(default=False)


class Project(BaseDocument):
    """Project model representing a graphic novel project."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    owner_id: PyObjectId
    status: ProjectStatus = Field(default=ProjectStatus.DRAFT)

    genre: Optional[str] = None
    target_audience: Optional[str] = None

    chapter_ids: List[PyObjectId] = Field(default_factory=list)
    character_ids: List[PyObjectId] = Field(default_factory=list)
    location_ids: List[PyObjectId] = Field(default_factory=list)
    instruction_ids: List[PyObjectId] = Field(default_factory=list)

    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    total_chapters: int = Field(default=0)
    total_scenes: int = Field(default=0)
    total_panels: int = Field(default=0)
    total_images: int = Field(default=0)

    is_published: bool = Field(default=False)
    published_at: Optional[datetime] = None

    class Config:
        collection_name = "projects"
        indexes = [
            {"fields": ["owner_id"]},
            {"fields": ["status"]},
            {"fields": ["created_at", "-1"]}
        ]