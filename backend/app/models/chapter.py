"""Chapter model for graphic novel chapters."""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import Field
from app.models.base import BaseDocument, PyObjectId


class ChapterStatus(str, Enum):
    """Chapter status enum."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"


class Chapter(BaseDocument):
    """Chapter model representing a chapter in a graphic novel."""

    project_id: PyObjectId
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    chapter_number: int = Field(..., ge=1)
    status: ChapterStatus = Field(default=ChapterStatus.DRAFT)

    scene_ids: List[PyObjectId] = Field(default_factory=list)
    instruction_ids: List[PyObjectId] = Field(default_factory=list)

    summary: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    total_scenes: int = Field(default=0)
    total_panels: int = Field(default=0)
    total_images: int = Field(default=0)

    is_locked: bool = Field(default=False)

    class Config:
        collection_name = "chapters"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["project_id", "chapter_number"], "unique": True},
            {"fields": ["status"]},
            {"fields": ["created_at", "-1"]}
        ]