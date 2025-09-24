"""Project repository with aggregation queries."""

from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.db.repositories.base import BaseRepository
from app.models import Project


class ProjectRepository(BaseRepository[Project]):
    """Repository for project operations with aggregations."""

    def __init__(self):
        super().__init__(Project)

    async def get_user_projects(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Project]:
        """Get all projects for a user."""
        return await self.list(
            filter={"owner_id": ObjectId(user_id)},
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]
        )

    async def get_project_with_stats(self, project_id: str) -> Optional[dict]:
        """Get project with computed statistics."""
        pipeline = [
            {"$match": {"_id": ObjectId(project_id)}},

            # Get chapter count
            {"$lookup": {
                "from": "chapters",
                "let": {"project_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$count": "total"}
                ],
                "as": "chapter_stats"
            }},

            # Get character count
            {"$lookup": {
                "from": "characters",
                "let": {"project_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$count": "total"}
                ],
                "as": "character_stats"
            }},

            # Get location count
            {"$lookup": {
                "from": "locations",
                "let": {"project_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$count": "total"}
                ],
                "as": "location_stats"
            }},

            # Get panel count (direct count across all panels)
            {"$lookup": {
                "from": "panels",
                "let": {"project_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$count": "total"}
                ],
                "as": "panel_stats"
            }},

            # Get image count
            {"$lookup": {
                "from": "images",
                "let": {"project_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }}
                ],
                "as": "image_stats"
            }},

            # Format the output
            {"$addFields": {
                "stats": {
                    "chapter_count": {"$ifNull": [{"$arrayElemAt": ["$chapter_stats.total", 0]}, 0]},
                    "character_count": {"$ifNull": [{"$arrayElemAt": ["$character_stats.total", 0]}, 0]},
                    "location_count": {"$ifNull": [{"$arrayElemAt": ["$location_stats.total", 0]}, 0]},
                    "panel_count": {"$ifNull": [{"$arrayElemAt": ["$panel_stats.total", 0]}, 0]},
                    "image_stats": "$image_stats"
                }
            }},

            # Clean up temporary fields
            {"$project": {
                "chapter_stats": 0,
                "character_stats": 0,
                "location_stats": 0,
                "panel_stats": 0,
                "image_stats": 0
            }}
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else None

    async def get_project_hierarchy(self, project_id: str) -> Optional[dict]:
        """Get project with full chapter/scene/panel hierarchy."""
        pipeline = [
            {"$match": {"_id": ObjectId(project_id)}},

            # Get chapters with scenes
            {"$lookup": {
                "from": "chapters",
                "let": {"project_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$sort": {"chapter_number": 1}},

                    # Get scenes for each chapter
                    {"$lookup": {
                        "from": "scenes",
                        "let": {"chapter_id": "$_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$chapter_id", "$$chapter_id"]}}},
                            {"$sort": {"scene_number": 1}},

                            # Get panel count for each scene
                            {"$lookup": {
                                "from": "panels",
                                "let": {"scene_id": "$_id"},
                                "pipeline": [
                                    {"$match": {"$expr": {"$eq": ["$scene_id", "$$scene_id"]}}},
                                    {"$count": "total"}
                                ],
                                "as": "panel_stats"
                            }},

                            {"$addFields": {
                                "panel_count": {"$ifNull": [{"$arrayElemAt": ["$panel_stats.total", 0]}, 0]}
                            }},

                            {"$project": {"panel_stats": 0}}
                        ],
                        "as": "scenes"
                    }},

                    {"$addFields": {
                        "scene_count": {"$size": "$scenes"},
                        "total_panels": {"$sum": "$scenes.panel_count"}
                    }}
                ],
                "as": "chapters"
            }},

            # Get characters
            {"$lookup": {
                "from": "characters",
                "localField": "_id",
                "foreignField": "project_id",
                "as": "characters"
            }},

            # Get locations
            {"$lookup": {
                "from": "locations",
                "localField": "_id",
                "foreignField": "project_id",
                "as": "locations"
            }}
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else None

    async def get_project_progress(self, project_id: str) -> dict:
        """Get detailed progress statistics for a project."""
        pipeline = [
            {"$match": {"_id": ObjectId(project_id)}},

            # Get chapter progress
            {"$lookup": {
                "from": "chapters",
                "let": {"project_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }}
                ],
                "as": "chapter_progress"
            }},

            # Get generation tasks
            {"$lookup": {
                "from": "generations",
                "let": {"project_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$group": {
                        "_id": {
                            "type": "$generation_type",
                            "status": "$status"
                        },
                        "count": {"$sum": 1}
                    }},
                    {"$group": {
                        "_id": "$_id.type",
                        "statuses": {
                            "$push": {
                                "status": "$_id.status",
                                "count": "$count"
                            }
                        }
                    }}
                ],
                "as": "generation_progress"
            }},

            # Format output
            {"$project": {
                "_id": 1,
                "name": 1,
                "status": 1,
                "progress": {
                    "chapters": "$chapter_progress",
                    "generations": "$generation_progress"
                }
            }}
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else {"progress": {"chapters": [], "generations": []}}

    async def update_project_status(self, project_id: str, status: str) -> bool:
        """Update project status."""
        result = await self.update(project_id, {"status": status})
        return result is not None


# Singleton instance
project_repository = ProjectRepository()