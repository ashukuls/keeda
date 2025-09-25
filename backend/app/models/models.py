"""Database models for Keeda."""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import Field
from app.models.base import BaseDocument, PyObjectId
from app.schemas.schemas import ProjectGenerationSettings


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


class Project(BaseDocument):
    """Project model for graphic novels."""

    # Database references
    user_id: PyObjectId = Field(..., description="User who owns this project")

    # Core content fields
    title: str = Field(..., description="Project title")
    genre: str = Field(..., description="Project genre")
    description: str = Field(..., description="Rich description with themes, plot, etc.")

    # User context
    user_input: str = Field(..., description="Original user story idea")
    generation_settings: Optional[ProjectGenerationSettings] = None

    # Status tracking
    status: ProjectStatus = Field(default="draft")

    # Settings
    default_llm_provider: str = Field(default="openai")
    default_image_provider: str = Field(default="dalle")

    class Config:
        collection_name = "projects"
        indexes = [
            {"fields": ["user_id"]},
            {"fields": ["status"]},
            {"fields": ["created_at", "-1"]}
        ]


class Chapter(BaseDocument):
    """Chapter model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")

    # Content fields
    chapter_number: int = Field(..., description="Sequential chapter number")
    title: str = Field(..., description="Chapter title")
    summary: str = Field(..., description="Chapter summary")

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


class Panel(BaseDocument):
    """Panel model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")
    chapter_id: PyObjectId = Field(..., description="Parent chapter ID")
    scene_id: PyObjectId = Field(..., description="Parent scene ID")

    # Content fields
    panel_number: int = Field(..., description="Sequential panel number within scene")
    shot_type: str = Field(..., description="Shot type: close_up, medium, wide, establishing")
    description: str = Field(..., description="Visual description")
    dialogue: Optional[str] = Field(None, description="Character dialogue")
    narration: Optional[str] = Field(None, description="Narrative text")

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


class Image(BaseDocument):
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


class Character(BaseDocument):
    """Character model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")

    # Content fields
    name: str = Field(..., description="Character name")
    role: str = Field(..., description="Role: protagonist/antagonist/supporting")
    description: str = Field(..., description="Character description with personality, relationships")
    biography: Optional[str] = Field(None, description="Detailed character profile")

    class Config:
        collection_name = "characters"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["project_id", "name"], "unique": True}
        ]


class Location(BaseDocument):
    """Location model."""

    # Database references
    project_id: PyObjectId = Field(..., description="Parent project ID")

    # Content fields
    name: str = Field(..., description="Location name")
    description: str = Field(..., description="Location description")

    class Config:
        collection_name = "locations"
        indexes = [
            {"fields": ["project_id"]},
            {"fields": ["project_id", "name"], "unique": True}
        ]


class Draft(BaseDocument):
    """Draft model for content variants."""

    # Database references
    project_id: Optional[PyObjectId] = Field(None, description="Parent project ID (optional for project drafts)")
    entity_type: str = Field(..., description="Type of entity (project_summary, character_list, scene_list, etc)")
    entity_id: Optional[PyObjectId] = Field(None, description="ID of the entity this draft is for")

    # Content
    type: str = Field(..., description="Draft type (e.g. project_summary, character_list)")
    content: Dict[str, Any] = Field(..., description="Draft content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

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


class ProjectInstruction(BaseDocument):
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