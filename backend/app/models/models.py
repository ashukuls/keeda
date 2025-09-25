"""Database models for Keeda."""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import Field
from app.models.base import BaseDocument, PyObjectId
from app.schemas.schemas import (
    ProjectContentSchema,
    ChapterContentSchema,
    SceneContentSchema,
    PanelContentSchema,
    CharacterContentSchema,
    LocationContentSchema,
    DraftContentSchema,
    ImagePromptSchema,
    InstructionContentSchema,
)


# Type aliases for database status fields
ProjectStatus = Literal["draft", "in_progress", "completed", "archived"]
ChapterStatus = Literal["draft", "in_progress", "completed"]
SceneType = Literal["action", "dialogue", "establishing"]
PanelType = Literal["close_up", "medium_shot", "wide_shot"]
ImageStatus = Literal["pending", "generating", "completed", "failed"]
DraftStatus = Literal["pending", "selected", "rejected"]
GenerationStatus = Literal["queued", "processing", "completed", "failed"]
InstructionLevel = Literal["project", "chapter", "scene"]


# Database Models
class User(BaseDocument):
    """User model with authentication."""

    username: str = Field(..., description="Unique username")
    hashed_password: str = Field(..., description="Hashed password")

    class Config:
        collection_name = "users"
        indexes = [
            {"fields": ["username"], "unique": True}
        ]


class Project(BaseDocument, ProjectContentSchema):
    """Project model for graphic novels."""

    # Database references
    owner_id: PyObjectId = Field(..., description="User who owns this project")

    # Status tracking
    status: ProjectStatus = Field(default="draft")

    # Settings
    default_llm_provider: str = Field(default="openai")
    default_image_provider: str = Field(default="dalle")

    class Config:
        collection_name = "projects"
        indexes = [
            {"fields": ["owner_id"]},
            {"fields": ["status"]},
            {"fields": ["created_at", "-1"]}
        ]


class Chapter(BaseDocument, ChapterContentSchema):
    """Chapter model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")

    # Status tracking
    status: ChapterStatus = Field(default="draft")

    class Config:
        collection_name = "chapters"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["project_id", "chapter_number"], "unique": True},
            {"fields": ["created_at", "-1"]}
        ]


class Scene(BaseDocument):
    """Scene model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")
    chapter_id: PyObjectId = Field(..., description="Parent chapter ID")

    # Content fields
    scene_number: int = Field(..., description="Sequential scene number within chapter")
    title: str = Field(..., description="Scene title")
    description: str = Field(..., description="Scene description with setting, mood, events")

    # Optional references
    location_id: Optional[PyObjectId] = None

    class Config:
        collection_name = "scenes"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["chapter_id"]},
            {"fields": ["chapter_id", "scene_number"], "unique": True},
            {"fields": ["created_at", "-1"]}
        ]


class Panel(BaseDocument, PanelContentSchema):
    """Panel model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")
    chapter_id: PyObjectId = Field(..., description="Parent chapter ID")
    scene_id: PyObjectId = Field(..., description="Parent scene ID")
    panel_number: int = Field(..., description="Sequential panel number within scene")

    # Selected content
    selected_image_id: Optional[PyObjectId] = None
    location_id: Optional[PyObjectId] = None

    class Config:
        collection_name = "panels"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["scene_id"]},
            {"fields": ["scene_id", "panel_number"], "unique": True},
            {"fields": ["created_at", "-1"]}
        ]


class Image(BaseDocument, ImagePromptSchema):
    """Image model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")
    panel_id: Optional[PyObjectId] = None
    character_id: Optional[PyObjectId] = None
    location_id: Optional[PyObjectId] = None

    # Status tracking
    status: ImageStatus = Field(default="pending")

    # File information
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    url: Optional[str] = None

    # Metadata
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

    # Generation details
    provider: Optional[str] = None
    model: Optional[str] = None
    generation_params: Dict[str, Any] = Field(default_factory=dict)

    # Error handling
    error_message: Optional[str] = None

    class Config:
        collection_name = "images"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["panel_id"]},
            {"fields": ["status"]},
            {"fields": ["created_at", "-1"]}
        ]


class Character(BaseDocument, CharacterContentSchema):
    """Character model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")

    class Config:
        collection_name = "characters"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["project_id", "name"], "unique": True}
        ]


class Location(BaseDocument, LocationContentSchema):
    """Location model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")

    class Config:
        collection_name = "locations"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["project_id", "name"], "unique": True}
        ]


class Draft(BaseDocument, DraftContentSchema):
    """Draft model for content variants."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")
    entity_type: str = Field(..., description="Type of entity (scene, panel, character)")
    entity_id: PyObjectId = Field(..., description="ID of the entity this draft is for")

    # Status tracking
    status: DraftStatus = Field(default="pending")

    # Generation metadata
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    generation_params: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        collection_name = "drafts"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["entity_type", "entity_id"]},
            {"fields": ["status"]},
            {"fields": ["created_at", "-1"]}
        ]


class Generation(BaseDocument):
    """Generation task tracking."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")
    user_id: PyObjectId = Field(..., description="User who initiated generation")

    # Task information
    generation_type: str = Field(..., description="Type of generation (text, image)")
    status: GenerationStatus = Field(default="queued")

    # Entity references
    entity_type: Optional[str] = None
    entity_id: Optional[PyObjectId] = None

    # Generation details
    prompt: str = Field(..., description="Generation prompt")
    provider: Optional[str] = None
    model: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Results
    result_id: Optional[PyObjectId] = None
    result_content: Optional[str] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)

    class Config:
        collection_name = "generations"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["user_id"]},
            {"fields": ["status"]},
            {"fields": ["created_at", "-1"]}
        ]


class ProjectInstruction(BaseDocument, InstructionContentSchema):
    """Project instruction model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")

    # Hierarchy
    level: InstructionLevel = Field(..., description="Instruction hierarchy level")
    parent_id: Optional[PyObjectId] = None
    entity_id: Optional[PyObjectId] = None  # Chapter/Scene/Panel ID if specific

    # Control flags
    is_active: bool = Field(default=True)
    applies_to_children: bool = Field(default=True)

    class Config:
        collection_name = "project_instructions"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["level"]},
            {"fields": ["entity_id"]},
            {"fields": ["priority", "-1"]}
        ]