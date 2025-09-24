"""Tests for database models."""

import pytest
from datetime import datetime
from bson import ObjectId

from app.models import (
    User, Project, Chapter, Scene, Panel,
    Character, Location, Draft, Generation,
    ProjectInstruction
)
from tests.conftest import assert_datetime_recent


class TestBaseDocument:
    """Test BaseDocument functionality."""

    async def test_base_document_timestamps(self, test_db):
        """Test that created_at and updated_at are set correctly."""
        from app.db.repositories.user import user_repository

        user = User(username="timestamps_test", hashed_password="test")
        created_user = await user_repository.create(user)

        assert created_user.id is not None
        assert isinstance(created_user.id, ObjectId)
        assert_datetime_recent(created_user.created_at)
        assert_datetime_recent(created_user.updated_at)
        assert created_user.schema_version == "1.0.0"

    async def test_base_document_dict_conversion(self, test_db):
        """Test dict conversion with ObjectId handling."""
        from app.db.repositories.user import user_repository

        user = User(username="dict_test", hashed_password="test")
        created_user = await user_repository.create(user)

        user_dict = created_user.dict()
        assert "_id" in user_dict
        assert isinstance(user_dict["_id"], str)  # ObjectId converted to string
        assert user_dict["username"] == "dict_test"


class TestUserModel:
    """Test User model."""

    async def test_user_creation(self, test_db):
        """Test creating a user."""
        from app.db.repositories.user import user_repository

        user = User(
            username="newuser",
            hashed_password="$2b$12$hashed"
        )
        created_user = await user_repository.create(user)

        assert created_user.username == "newuser"
        assert created_user.hashed_password == "$2b$12$hashed"

    async def test_user_unique_username(self, test_db):
        """Test that username must be unique."""
        from app.db.repositories.user import user_repository

        user1 = User(username="unique_test", hashed_password="test1")
        await user_repository.create(user1)

        user2 = User(username="unique_test", hashed_password="test2")
        with pytest.raises(ValueError, match="unique field already exists"):
            await user_repository.create(user2)


class TestProjectModel:
    """Test Project model."""

    async def test_project_creation(self, test_user, test_db):
        """Test creating a project."""
        from app.db.repositories.project import project_repository

        project = Project(
            name="Test Project",
            description="A test graphic novel",
            owner_id=test_user.id,
            genre="Fantasy",
            target_audience="Adults"
        )
        created_project = await project_repository.create(project)

        assert created_project.name == "Test Project"
        assert created_project.owner_id == test_user.id
        assert created_project.status == "draft"
        assert created_project.default_llm_provider == "openai"
        assert created_project.default_image_provider == "dalle"

    async def test_project_status_enum(self, test_user, test_db):
        """Test project status enum values."""
        from app.db.repositories.project import project_repository

        project = Project(
            name="Status Test",
            owner_id=test_user.id,
            status="in_progress"
        )
        created_project = await project_repository.create(project)

        assert created_project.status == "in_progress"


class TestContentModels:
    """Test Chapter, Scene, and Panel models."""

    async def test_chapter_creation(self, test_project, test_db):
        """Test creating a chapter."""
        from app.db.repositories.content import chapter_repository

        chapter = Chapter(
            project_id=test_project.id,
            chapter_number=1,
            title="Chapter One",
            description="The beginning"
        )
        created_chapter = await chapter_repository.create(chapter)

        assert created_chapter.project_id == test_project.id
        assert created_chapter.chapter_number == 1
        assert created_chapter.title == "Chapter One"
        assert created_chapter.status == "draft"

    async def test_scene_creation(self, test_project, test_chapter, test_db):
        """Test creating a scene."""
        from app.db.repositories.content import scene_repository

        scene = Scene(
            project_id=test_project.id,
            chapter_id=test_chapter.id,
            scene_number=1,
            title="Opening",
            setting="A dark forest",
            mood="Ominous",
            scene_type="establishing"
        )
        created_scene = await scene_repository.create(scene)

        assert created_scene.chapter_id == test_chapter.id
        assert created_scene.scene_number == 1
        assert created_scene.scene_type == "establishing"
        assert created_scene.location_id is None  # Optional field

    async def test_panel_creation(self, test_project, test_chapter, test_scene, test_db):
        """Test creating a panel."""
        from app.db.repositories.content import panel_repository

        panel = Panel(
            project_id=test_project.id,
            chapter_id=test_chapter.id,
            scene_id=test_scene.id,
            panel_number=1,
            description="A wide establishing shot",
            panel_type="wide_shot",
            dialogue=[
                {"character": "Hero", "text": "Where am I?"},
                {"character": "Villain", "text": "Welcome to my domain!"}
            ],
            narration="The forest was darker than night itself."
        )
        created_panel = await panel_repository.create(panel)

        assert created_panel.scene_id == test_scene.id
        assert created_panel.panel_number == 1
        assert created_panel.panel_type == "wide_shot"
        assert len(created_panel.dialogue) == 2
        assert created_panel.dialogue[0]["character"] == "Hero"
        assert created_panel.selected_image_id is None  # No image selected yet


class TestCharacterLocationModels:
    """Test Character and Location models."""

    async def test_character_creation(self, test_project, test_db):
        """Test creating a character."""
        from app.db.repositories.base import BaseRepository
        from app.models import Character

        char_repo = BaseRepository(Character)

        character = Character(
            project_id=test_project.id,
            name="Hero",
            description="The main protagonist",
            appearance="Tall, dark hair, blue eyes",
            personality="Brave but impulsive",
            background="Orphaned at young age",
            visual_description="Wears a long coat and carries a sword"
        )
        created_character = await char_repo.create(character)

        assert created_character.project_id == test_project.id
        assert created_character.name == "Hero"
        assert created_character.appearance == "Tall, dark hair, blue eyes"

    async def test_location_creation(self, test_project, test_db):
        """Test creating a location."""
        from app.db.repositories.base import BaseRepository
        from app.models import Location

        loc_repo = BaseRepository(Location)

        location = Location(
            project_id=test_project.id,
            name="Dark Forest",
            description="An ancient forest shrouded in mystery",
            atmosphere="Eerie and foreboding",
            key_features=["Giant trees", "Fog", "Hidden paths"],
            visual_description="Towering black trees with twisted branches"
        )
        created_location = await loc_repo.create(location)

        assert created_location.project_id == test_project.id
        assert created_location.name == "Dark Forest"
        assert len(created_location.key_features) == 3
        assert "Fog" in created_location.key_features


class TestDraftGenerationModels:
    """Test Draft and Generation models."""

    async def test_draft_creation(self, test_project, test_panel, test_db):
        """Test creating a draft."""
        from app.db.repositories.base import BaseRepository
        from app.models import Draft

        draft_repo = BaseRepository(Draft)

        draft = Draft(
            project_id=test_project.id,
            entity_type="panel",
            entity_id=test_panel.id,
            content="A detailed description of the panel...",
            prompt="Describe this panel in detail",
            status="pending",
            llm_provider="openai",
            llm_model="gpt-4"
        )
        created_draft = await draft_repo.create(draft)

        assert created_draft.entity_type == "panel"
        assert created_draft.entity_id == test_panel.id
        assert created_draft.status == "pending"

    async def test_generation_tracking(self, test_project, test_user, test_db):
        """Test generation task tracking."""
        from app.db.repositories.base import BaseRepository
        from app.models import Generation

        gen_repo = BaseRepository(Generation)

        generation = Generation(
            project_id=test_project.id,
            user_id=test_user.id,
            generation_type="text",
            status="queued",
            prompt="Generate a scene description",
            provider="anthropic",
            model="claude-3"
        )
        created_generation = await gen_repo.create(generation)

        assert created_generation.generation_type == "text"
        assert created_generation.status == "queued"
        assert created_generation.retry_count == 0
        assert created_generation.error_message is None


class TestProjectInstruction:
    """Test ProjectInstruction model."""

    async def test_instruction_creation(self, test_project, test_db):
        """Test creating project instructions."""
        from app.db.repositories.base import BaseRepository
        from app.models import ProjectInstruction

        inst_repo = BaseRepository(ProjectInstruction)

        instruction = ProjectInstruction(
            project_id=test_project.id,
            level="project",
            title="Art Style",
            content="Use a noir comic book style with high contrast",
            priority=5,
            is_active=True,
            applies_to_children=True
        )
        created_instruction = await inst_repo.create(instruction)

        assert created_instruction.level == "project"
        assert created_instruction.priority == 5
        assert created_instruction.is_active is True
        assert created_instruction.applies_to_children is True