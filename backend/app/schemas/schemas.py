"""Schemas for LLM agent outputs and content models.

Minimal schemas with essential fields only.
Rich information is stored in text fields like summary/description.
"""

from typing import List, Optional, Dict, Union
from pydantic import BaseModel
from enum import Enum


# ============================================================================
# List Generation Schemas
# ============================================================================

class ProjectSummary(BaseModel):
    """Output from ProjectSummaryAgent"""
    title: str
    genre: str
    description: str  # Rich text containing themes, story, etc.


class CharacterListItem(BaseModel):
    """Single character in list"""
    name: str
    role: str  # protagonist, antagonist, supporting
    description: str  # Rich text with brief, relationships, etc.


class CharacterList(BaseModel):
    """Output from CharacterListAgent"""
    characters: List[CharacterListItem]


class ChapterListItem(BaseModel):
    """Single chapter in list"""
    number: int
    title: str
    summary: str  # Rich text with events, plot points, etc.


class ChapterList(BaseModel):
    """Output from ChapterListAgent"""
    chapters: List[ChapterListItem]


class SceneListItem(BaseModel):
    """Single scene in list"""
    number: int
    title: str
    description: str  # Rich text with setting, mood, events, etc.


class SceneList(BaseModel):
    """Output from SceneListAgent"""
    scenes: List[SceneListItem]


class PanelListItem(BaseModel):
    """Single panel in list"""
    number: int
    shot_type: str  # close_up, medium, wide, establishing
    description: str  # Rich text with visuals, action, etc.
    dialogue: Optional[str] = None  # Combined dialogue text
    narration: Optional[str] = None


class PanelList(BaseModel):
    """Output from PanelListAgent"""
    panels: List[PanelListItem]


# ============================================================================
# Detail Enhancement Schemas
# ============================================================================

class CharacterProfile(BaseModel):
    """Output from CharacterProfileAgent"""
    name: str
    biography: str  # Rich text with full character details


class SceneSummary(BaseModel):
    """Output from SceneSummaryAgent"""
    summary: str  # Rich text with all scene details


class ImagePrompt(BaseModel):
    """Output from VisualPromptAgent"""
    prompt: str  # Complete prompt for image generation
    negative_prompt: Optional[str] = None


# ============================================================================
# Agent Types and Generation Settings
# ============================================================================

class AgentType(str, Enum):
    """Types of agents in the system."""
    # List generation agents
    PROJECT_SUMMARY = "project_summary"
    CHARACTER_LIST = "character_list"
    CHAPTER_LIST = "chapter_list"
    SCENE_LIST = "scene_list"
    PANEL_LIST = "panel_list"

    # Detail enhancement agents
    CHARACTER_PROFILE = "character_profile"
    SCENE_SUMMARY = "scene_summary"
    VISUAL_PROMPT = "visual_prompt"


class GenerationMode(str, Enum):
    """Generation modes for agents."""
    DIRECT = "direct"  # Save directly to database
    REVIEW = "review"  # Save to drafts first, require approval


class ProjectGenerationSettings(BaseModel):
    """Per-project settings for agent generation."""
    user_instructions: str = ""  # Natural language instructions from user
    agent_modes: Dict[str, GenerationMode] = {}  # Mode per agent type (using AgentType.value as key)

    # Optional specific settings
    num_characters: Optional[int] = 3
    num_chapters: Optional[int] = 2
    num_scenes_per_chapter: Optional[int] = 2
    num_panels_per_scene: Optional[int] = 3

    visual_style: Optional[str] = "comic book art"

    def get_mode(self, agent_type: Union[str, AgentType]) -> GenerationMode:
        """Get generation mode for specific agent type."""
        # Handle both string and AgentType enum
        key = agent_type.value if hasattr(agent_type, 'value') else agent_type
        return self.agent_modes.get(key, GenerationMode.REVIEW)