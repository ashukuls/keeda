"""Schemas for LLM agent outputs.

Minimal schemas with essential fields only.
Rich information is stored in text fields like summary/description.
"""

from typing import List, Optional
from pydantic import BaseModel


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