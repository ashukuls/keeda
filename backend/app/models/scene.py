"""Scene model for graphic novel scenes."""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import Field
from app.models.base import BaseDocument, PyObjectId


class SceneType(str, Enum):
    """Scene type enum."""
    ACTION = "action"
    DIALOGUE = "dialogue"
    NARRATIVE = "narrative"
    TRANSITION = "transition"
    ESTABLISHING = "establishing"


class Scene(BaseDocument):
    """Scene model representing a scene within a chapter."""

    project_id: PyObjectId
    chapter_id: PyObjectId
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    scene_number: int = Field(..., ge=1)
    scene_type: SceneType = Field(default=SceneType.ACTION)

    panel_ids: List[PyObjectId] = Field(default_factory=list)
    character_ids: List[PyObjectId] = Field(default_factory=list)
    location_id: Optional[PyObjectId] = None

    setting: Optional[str] = None
    time_of_day: Optional[str] = None
    mood: Optional[str] = None
    summary: Optional[str] = None
    dialogue_snippet: Optional[str] = None
    notes: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    total_panels: int = Field(default=0)
    total_images: int = Field(default=0)

    is_locked: bool = Field(default=False)

    class Config:
        collection_name = "scenes"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["chapter_id"]},
            {"fields": ["chapter_id", "scene_number"], "unique": True},
            {"fields": ["scene_type"]},
            {"fields": ["created_at", "-1"]}
        ]