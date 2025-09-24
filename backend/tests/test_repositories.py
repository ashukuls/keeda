"""Tests for repository operations and aggregations."""

import pytest
from bson import ObjectId

from app.models import Project, Chapter, Scene, Panel
from app.db.repositories.user import user_repository
from app.db.repositories.project import project_repository
from app.db.repositories.content import chapter_repository, scene_repository, panel_repository


class TestUserRepository:
    """Test user repository operations."""

    async def test_get_by_username(self, test_db, test_user):
        """Test getting user by username."""
        user = await user_repository.get_by_username("testuser")
        assert user is not None
        assert user.id == test_user.id
        assert user.username == "testuser"

    async def test_username_exists(self, test_db, test_user):
        """Test checking if username exists."""
        exists = await user_repository.username_exists("testuser")
        assert exists is True

        not_exists = await user_repository.username_exists("nonexistent")
        assert not_exists is False

    async def test_get_user_projects_count(self, test_db, test_user, test_project):
        """Test getting count of user's projects."""
        count = await user_repository.get_user_projects_count(str(test_user.id))
        assert count == 1

        # Create another project
        project2 = Project(
            name="Second Project",
            owner_id=test_user.id
        )
        await project_repository.create(project2)

        count = await user_repository.get_user_projects_count(str(test_user.id))
        assert count == 2

    async def test_get_user_with_stats(self, test_db, test_user, test_project):
        """Test getting user with aggregated statistics."""
        user_stats = await user_repository.get_user_with_stats(str(test_user.id))

        assert user_stats is not None
        assert user_stats["username"] == "testuser"
        assert user_stats["project_count"] == 1
        assert user_stats["active_projects"] == 0  # Default status is DRAFT
        assert "hashed_password" not in user_stats  # Password excluded


class TestProjectRepository:
    """Test project repository operations."""

    async def test_get_user_projects(self, test_db, test_user):
        """Test getting all projects for a user."""
        # Create multiple projects
        for i in range(3):
            project = Project(
                name=f"Project {i}",
                owner_id=test_user.id
            )
            await project_repository.create(project)

        projects = await project_repository.get_user_projects(str(test_user.id))
        assert len(projects) == 3
        # Should be ordered by created_at descending
        assert projects[0].name == "Project 2"

    async def test_get_project_with_stats(self, test_db, sample_hierarchy):
        """Test getting project with computed statistics."""
        stats = await project_repository.get_project_with_stats(str(sample_hierarchy.id))

        assert stats is not None
        assert stats["name"] == "Complex Project"
        assert stats["stats"]["chapter_count"] == 3
        assert stats["stats"]["panel_count"] == 18  # 3 chapters * 2 scenes * 3 panels

    async def test_get_project_hierarchy(self, test_db, sample_hierarchy):
        """Test getting full project hierarchy."""
        hierarchy = await project_repository.get_project_hierarchy(str(sample_hierarchy.id))

        assert hierarchy is not None
        assert len(hierarchy["chapters"]) == 3

        # Check first chapter
        first_chapter = hierarchy["chapters"][0]
        assert first_chapter["chapter_number"] == 1
        assert len(first_chapter["scenes"]) == 2
        assert first_chapter["scene_count"] == 2
        assert first_chapter["total_panels"] == 6

        # Check first scene
        first_scene = first_chapter["scenes"][0]
        assert first_scene["scene_number"] == 1
        assert first_scene["panel_count"] == 3

    async def test_get_project_progress(self, test_db, sample_hierarchy):
        """Test getting project progress statistics."""
        # Update some chapters to different statuses
        chapters = await chapter_repository.get_project_chapters(str(sample_hierarchy.id))
        await chapter_repository.update(
            str(chapters[0].id),
            {"status": "in_progress"}
        )
        await chapter_repository.update(
            str(chapters[1].id),
            {"status": "completed"}
        )

        progress = await project_repository.get_project_progress(str(sample_hierarchy.id))

        assert progress is not None
        assert "progress" in progress
        chapter_progress = progress["progress"]["chapters"]

        # Check status counts
        status_counts = {item["_id"]: item["count"] for item in chapter_progress}
        assert status_counts.get("draft") == 1
        assert status_counts.get("in_progress") == 1
        assert status_counts.get("completed") == 1

    async def test_update_project_status(self, test_db, test_project):
        """Test updating project status."""
        success = await project_repository.update_project_status(
            str(test_project.id),
            "in_progress"
        )
        assert success is True

        # Verify the update
        updated = await project_repository.get(str(test_project.id))
        assert updated.status == "in_progress"


class TestContentRepositories:
    """Test chapter, scene, and panel repositories."""

    async def test_get_project_chapters(self, test_db, sample_hierarchy):
        """Test getting all chapters for a project."""
        chapters = await chapter_repository.get_project_chapters(str(sample_hierarchy.id))

        assert len(chapters) == 3
        # Should be ordered by chapter_number
        assert chapters[0].chapter_number == 1
        assert chapters[1].chapter_number == 2
        assert chapters[2].chapter_number == 3

    async def test_get_chapter_with_scenes(self, test_db, sample_hierarchy):
        """Test getting chapter with all its scenes."""
        chapters = await chapter_repository.get_project_chapters(str(sample_hierarchy.id))
        first_chapter = chapters[0]

        chapter_data = await chapter_repository.get_chapter_with_scenes(str(first_chapter.id))

        assert chapter_data is not None
        assert len(chapter_data["scenes"]) == 2
        assert chapter_data["scene_count"] == 2
        assert chapter_data["total_panels"] == 6

        # Check scene details
        first_scene = chapter_data["scenes"][0]
        assert first_scene["scene_number"] == 1
        assert first_scene["panel_count"] == 3

    async def test_get_next_chapter_number(self, test_db, sample_hierarchy):
        """Test auto-incrementing chapter numbers."""
        next_num = await chapter_repository.get_next_chapter_number(str(sample_hierarchy.id))
        assert next_num == 4  # Already has 3 chapters

        # For a project with no chapters
        new_project = Project(
            name="Empty Project",
            owner_id=sample_hierarchy.owner_id
        )
        new_project = await project_repository.create(new_project)
        next_num = await chapter_repository.get_next_chapter_number(str(new_project.id))
        assert next_num == 1

    async def test_get_scene_with_panels(self, test_db, sample_hierarchy):
        """Test getting scene with all its panels."""
        chapters = await chapter_repository.get_project_chapters(str(sample_hierarchy.id))
        scenes = await scene_repository.get_chapter_scenes(str(chapters[0].id))
        first_scene = scenes[0]

        scene_data = await scene_repository.get_scene_with_panels(str(first_scene.id))

        assert scene_data is not None
        assert len(scene_data["panels"]) == 3
        assert scene_data["panel_count"] == 3

        # Check panel details
        first_panel = scene_data["panels"][0]
        assert first_panel["panel_number"] == 1
        assert first_panel["draft_count"] == 0  # No drafts created yet

    async def test_get_next_scene_number(self, test_db, sample_hierarchy):
        """Test auto-incrementing scene numbers."""
        chapters = await chapter_repository.get_project_chapters(str(sample_hierarchy.id))
        next_num = await scene_repository.get_next_scene_number(str(chapters[0].id))
        assert next_num == 3  # Already has 2 scenes

    async def test_get_panel_with_content(self, test_db, test_panel):
        """Test getting panel with all associated content."""
        panel_data = await panel_repository.get_panel_with_content(str(test_panel.id))

        assert panel_data is not None
        assert panel_data["panel_number"] == 1
        assert panel_data["image_count"] == 0  # No images yet
        assert panel_data["draft_count"] == 0  # No drafts yet
        assert len(panel_data["images"]) == 0
        assert len(panel_data["drafts"]) == 0

    async def test_get_next_panel_number(self, test_db, sample_hierarchy):
        """Test auto-incrementing panel numbers."""
        chapters = await chapter_repository.get_project_chapters(str(sample_hierarchy.id))
        scenes = await scene_repository.get_chapter_scenes(str(chapters[0].id))
        next_num = await panel_repository.get_next_panel_number(str(scenes[0].id))
        assert next_num == 4  # Already has 3 panels

    async def test_get_panels_needing_images(self, test_db, sample_hierarchy):
        """Test finding panels without selected images."""
        panels = await panel_repository.get_panels_needing_images(str(sample_hierarchy.id))

        assert len(panels) == 10  # Limited to 10 by default
        # All panels should have no selected image
        for panel in panels:
            assert panel["selected_image_id"] is None
            assert "scene" in panel
            assert "chapter" in panel


class TestAggregations:
    """Test aggregation utilities."""

    async def test_aggregation_builder(self, test_db):
        """Test the aggregation builder utility."""
        from app.db.aggregations import build_aggregation

        pipeline = (
            build_aggregation()
            .match({"status": "active"})
            .lookup("chapters", "_id", "project_id", "chapters")
            .add_fields({"chapter_count": {"$size": "$chapters"}})
            .sort([("created_at", -1)])
            .limit(10)
            .build()
        )

        assert len(pipeline) == 5
        assert pipeline[0] == {"$match": {"status": "active"}}
        assert pipeline[1]["$lookup"]["from"] == "chapters"
        assert pipeline[3]["$sort"]["created_at"] == -1
        assert pipeline[4] == {"$limit": 10}

    async def test_content_stats_aggregation(self, test_db, sample_hierarchy):
        """Test content statistics aggregation."""
        from app.db.aggregations import CommonAggregations
        from app.db.database import get_collection

        # Run the aggregation
        pipeline = CommonAggregations.get_content_stats_pipeline(str(sample_hierarchy.id))

        # We need to run this on multiple collections, so let's test the structure
        assert len(pipeline) > 0
        assert "$facet" in pipeline[0]
        assert "chapters" in pipeline[0]["$facet"]
        assert "scenes" in pipeline[0]["$facet"]
        assert "panels" in pipeline[0]["$facet"]

    async def test_search_content_pipeline(self, test_db, sample_hierarchy):
        """Test search across content aggregation."""
        from app.db.aggregations import CommonAggregations

        pipeline = CommonAggregations.search_content_pipeline(
            str(sample_hierarchy.id),
            "Chapter"
        )

        assert len(pipeline) > 0
        assert "$facet" in pipeline[0]
        facet = pipeline[0]["$facet"]
        assert "chapters" in facet
        assert "scenes" in facet
        assert "panels" in facet
        assert "characters" in facet

        # Check that search uses regex
        chapter_match = facet["chapters"][0]["$match"]
        assert "$or" in chapter_match
        or_conditions = chapter_match["$or"]
        assert any("$regex" in str(cond) for cond in or_conditions)