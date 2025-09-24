"""Test configuration and fixtures."""

import asyncio
import pytest
from typing import Generator, AsyncGenerator
from pymongo import MongoClient
from pymongo.database import Database
import os
from datetime import datetime

from app.core.config import settings
from app.db.database import MongoDB
from app.models import User, Project, Chapter, Scene, Panel


# Override settings for testing
settings.DATABASE_NAME = settings.TEST_DATABASE_NAME
# TEST_MONGODB_URL is now computed from environment variables


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_teardown():
    """Setup and teardown for all tests."""
    # Setup
    MongoDB.connect()
    yield
    # Teardown
    MongoDB.disconnect()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[Database, None]:
    """Provide clean test database for each test."""
    # Get the already connected database
    db = MongoDB.get_database()

    # Clear all collections before test
    for collection_name in db.list_collection_names():
        db[collection_name].delete_many({})

    yield db

    # Clear all collections after test
    for collection_name in db.list_collection_names():
        db[collection_name].delete_many({})


@pytest.fixture
async def test_user(test_db) -> User:
    """Create a test user."""
    from app.db.repositories.user import user_repository

    user = User(
        username="testuser",
        hashed_password="$2b$12$test_hashed_password"
    )
    created_user = await user_repository.create(user)
    return created_user


@pytest.fixture
async def test_project(test_db, test_user) -> Project:
    """Create a test project."""
    from app.db.repositories.project import project_repository

    project = Project(
        name="Test Graphic Novel",
        description="A test project for unit testing",
        owner_id=test_user.id,
        genre="Science Fiction",
        target_audience="Young Adults"
    )
    created_project = await project_repository.create(project)
    return created_project


@pytest.fixture
async def test_chapter(test_db, test_project) -> Chapter:
    """Create a test chapter."""
    from app.db.repositories.content import chapter_repository

    chapter = Chapter(
        project_id=test_project.id,
        chapter_number=1,
        title="The Beginning",
        description="The first chapter of our story"
    )
    created_chapter = await chapter_repository.create(chapter)
    return created_chapter


@pytest.fixture
async def test_scene(test_db, test_project, test_chapter) -> Scene:
    """Create a test scene."""
    from app.db.repositories.content import scene_repository

    scene = Scene(
        project_id=test_project.id,
        chapter_id=test_chapter.id,
        scene_number=1,
        title="Opening Scene",
        setting="A futuristic city at dawn",
        mood="Mysterious",
        scene_type="establishing"
    )
    created_scene = await scene_repository.create(scene)
    return created_scene


@pytest.fixture
async def test_panel(test_db, test_project, test_chapter, test_scene) -> Panel:
    """Create a test panel."""
    from app.db.repositories.content import panel_repository

    panel = Panel(
        project_id=test_project.id,
        chapter_id=test_chapter.id,
        scene_id=test_scene.id,
        panel_number=1,
        description="Wide shot of the city skyline with hovering vehicles",
        panel_type="wide_shot",
        dialogue=[
            {"character": "Narrator", "text": "The year is 2150..."}
        ],
        narration="The city never sleeps."
    )
    created_panel = await panel_repository.create(panel)
    return created_panel


@pytest.fixture
async def sample_hierarchy(test_db, test_user):
    """Create a sample project hierarchy with multiple chapters, scenes, and panels."""
    from app.db.repositories.project import project_repository
    from app.db.repositories.content import chapter_repository, scene_repository, panel_repository

    # Create project
    project = Project(
        name="Complex Project",
        description="A project with full hierarchy",
        owner_id=test_user.id
    )
    project = await project_repository.create(project)

    # Create 3 chapters
    for ch_num in range(1, 4):
        chapter = Chapter(
            project_id=project.id,
            chapter_number=ch_num,
            title=f"Chapter {ch_num}",
            description=f"Description for chapter {ch_num}"
        )
        chapter = await chapter_repository.create(chapter)

        # Create 2 scenes per chapter
        for sc_num in range(1, 3):
            scene = Scene(
                project_id=project.id,
                chapter_id=chapter.id,
                scene_number=sc_num,
                title=f"Scene {ch_num}.{sc_num}",
                setting=f"Setting for scene {sc_num}",
                scene_type="action" if sc_num == 1 else "dialogue"
            )
            scene = await scene_repository.create(scene)

            # Create 3 panels per scene
            for pn_num in range(1, 4):
                panel = Panel(
                    project_id=project.id,
                    chapter_id=chapter.id,
                    scene_id=scene.id,
                    panel_number=pn_num,
                    description=f"Panel {pn_num} in scene {sc_num}",
                    panel_type="medium_shot" if pn_num == 2 else "close_up"
                )
                await panel_repository.create(panel)

    return project


# Utility functions for testing
def assert_datetime_recent(dt: datetime, seconds: int = 5):
    """Assert that a datetime is recent (within specified seconds)."""
    if dt is None:
        raise AssertionError("Datetime is None")

    diff = (datetime.utcnow() - dt).total_seconds()
    if diff > seconds:
        raise AssertionError(f"Datetime {dt} is not recent (diff: {diff}s)")