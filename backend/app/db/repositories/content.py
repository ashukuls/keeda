"""Content repository for chapters, scenes, and panels."""

from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.db.repositories.base import BaseRepository
from app.models import Chapter, Scene, Panel


class ChapterRepository(BaseRepository[Chapter]):
    """Repository for chapter operations."""

    def __init__(self):
        super().__init__(Chapter)

    async def get_project_chapters(self, project_id: str) -> List[Chapter]:
        """Get all chapters for a project, ordered by chapter number."""
        return await self.list(
            filter={"project_id": ObjectId(project_id)},
            sort=[("chapter_number", 1)]
        )

    async def get_chapter_with_scenes(self, chapter_id: str) -> Optional[dict]:
        """Get chapter with all its scenes."""
        pipeline = [
            {"$match": {"_id": ObjectId(chapter_id)}},

            # Get scenes
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

            # Get instructions
            {"$lookup": {
                "from": "project_instructions",
                "let": {"chapter_id": "$_id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$entity_id", "$$chapter_id"]},
                                {"$eq": ["$level", "chapter"]}
                            ]
                        }
                    }},
                    {"$sort": {"priority": -1}}
                ],
                "as": "instructions"
            }},

            # Add statistics
            {"$addFields": {
                "scene_count": {"$size": "$scenes"},
                "total_panels": {"$sum": "$scenes.panel_count"}
            }}
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else None

    async def get_next_chapter_number(self, project_id: str) -> int:
        """Get the next available chapter number for a project."""
        pipeline = [
            {"$match": {"project_id": ObjectId(project_id)}},
            {"$group": {"_id": None, "max_number": {"$max": "$chapter_number"}}},
        ]
        result = list(self.collection.aggregate(pipeline))
        if result and result[0].get("max_number"):
            return result[0]["max_number"] + 1
        return 1


class SceneRepository(BaseRepository[Scene]):
    """Repository for scene operations."""

    def __init__(self):
        super().__init__(Scene)

    async def get_chapter_scenes(self, chapter_id: str) -> List[Scene]:
        """Get all scenes for a chapter, ordered by scene number."""
        return await self.list(
            filter={"chapter_id": ObjectId(chapter_id)},
            sort=[("scene_number", 1)]
        )

    async def get_scene_with_panels(self, scene_id: str) -> Optional[dict]:
        """Get scene with all its panels and related data."""
        pipeline = [
            {"$match": {"_id": ObjectId(scene_id)}},

            # Get panels
            {"$lookup": {
                "from": "panels",
                "let": {"scene_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$scene_id", "$$scene_id"]}}},
                    {"$sort": {"panel_number": 1}},

                    # Get selected image for each panel
                    {"$lookup": {
                        "from": "images",
                        "let": {"image_id": "$selected_image_id"},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$_id", "$$image_id"]}}}
                        ],
                        "as": "selected_image"
                    }},

                    # Get draft count
                    {"$lookup": {
                        "from": "drafts",
                        "let": {"panel_id": "$_id"},
                        "pipeline": [
                            {"$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$entity_id", "$$panel_id"]},
                                        {"$eq": ["$entity_type", "panel"]}
                                    ]
                                }
                            }},
                            {"$count": "total"}
                        ],
                        "as": "draft_stats"
                    }},

                    {"$addFields": {
                        "selected_image": {"$arrayElemAt": ["$selected_image", 0]},
                        "draft_count": {"$ifNull": [{"$arrayElemAt": ["$draft_stats.total", 0]}, 0]}
                    }},

                    {"$project": {"draft_stats": 0}}
                ],
                "as": "panels"
            }},

            # Get location if referenced
            {"$lookup": {
                "from": "locations",
                "localField": "location_id",
                "foreignField": "_id",
                "as": "location"
            }},

            # Get characters in scene
            {"$lookup": {
                "from": "panels",
                "let": {"scene_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$scene_id", "$$scene_id"]}}},
                    {"$project": {"dialogue": 1}},
                    {"$unwind": {"path": "$dialogue", "preserveNullAndEmptyArrays": True}},
                    {"$group": {
                        "_id": "$dialogue.character",
                        "dialogue_count": {"$sum": 1}
                    }},
                    {"$match": {"_id": {"$ne": None}}}
                ],
                "as": "character_dialogue"
            }},

            # Format output
            {"$addFields": {
                "location": {"$arrayElemAt": ["$location", 0]},
                "panel_count": {"$size": "$panels"}
            }}
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else None

    async def get_next_scene_number(self, chapter_id: str) -> int:
        """Get the next available scene number for a chapter."""
        pipeline = [
            {"$match": {"chapter_id": ObjectId(chapter_id)}},
            {"$group": {"_id": None, "max_number": {"$max": "$scene_number"}}},
        ]
        result = list(self.collection.aggregate(pipeline))
        if result and result[0].get("max_number"):
            return result[0]["max_number"] + 1
        return 1


class PanelRepository(BaseRepository[Panel]):
    """Repository for panel operations."""

    def __init__(self):
        super().__init__(Panel)

    async def get_scene_panels(self, scene_id: str) -> List[Panel]:
        """Get all panels for a scene, ordered by panel number."""
        return await self.list(
            filter={"scene_id": ObjectId(scene_id)},
            sort=[("panel_number", 1)]
        )

    async def get_panel_with_content(self, panel_id: str) -> Optional[dict]:
        """Get panel with all associated content."""
        pipeline = [
            {"$match": {"_id": ObjectId(panel_id)}},

            # Get all images for this panel
            {"$lookup": {
                "from": "images",
                "let": {"panel_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$panel_id", "$$panel_id"]}}},
                    {"$sort": {"created_at": -1}}
                ],
                "as": "images"
            }},

            # Get all drafts
            {"$lookup": {
                "from": "drafts",
                "let": {"panel_id": "$_id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$entity_id", "$$panel_id"]},
                                {"$eq": ["$entity_type", "panel"]}
                            ]
                        }
                    }},
                    {"$sort": {"created_at": -1}}
                ],
                "as": "drafts"
            }},

            # Get location if referenced
            {"$lookup": {
                "from": "locations",
                "localField": "location_id",
                "foreignField": "_id",
                "as": "location"
            }},

            # Get referenced characters
            {"$lookup": {
                "from": "characters",
                "let": {"project_id": "$project_id", "dialogue": "$dialogue"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$project_id", "$$project_id"]}}},
                    {"$match": {
                        "$expr": {
                            "$in": ["$name", {"$ifNull": [
                                {"$map": {
                                    "input": "$$dialogue",
                                    "as": "d",
                                    "in": "$$d.character"
                                }},
                                []
                            ]}]
                        }
                    }}
                ],
                "as": "characters"
            }},

            # Format output
            {"$addFields": {
                "location": {"$arrayElemAt": ["$location", 0]},
                "image_count": {"$size": "$images"},
                "draft_count": {"$size": "$drafts"}
            }}
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else None

    async def get_next_panel_number(self, scene_id: str) -> int:
        """Get the next available panel number for a scene."""
        pipeline = [
            {"$match": {"scene_id": ObjectId(scene_id)}},
            {"$group": {"_id": None, "max_number": {"$max": "$panel_number"}}},
        ]
        result = list(self.collection.aggregate(pipeline))
        if result and result[0].get("max_number"):
            return result[0]["max_number"] + 1
        return 1

    async def get_panels_needing_images(self, project_id: str, limit: int = 10) -> List[dict]:
        """Get panels that don't have selected images yet."""
        pipeline = [
            {"$match": {
                "project_id": ObjectId(project_id),
                "selected_image_id": None
            }},
            {"$sort": {"created_at": 1}},
            {"$limit": limit},

            # Get scene info
            {"$lookup": {
                "from": "scenes",
                "localField": "scene_id",
                "foreignField": "_id",
                "as": "scene"
            }},

            # Get chapter info
            {"$lookup": {
                "from": "chapters",
                "localField": "chapter_id",
                "foreignField": "_id",
                "as": "chapter"
            }},

            {"$addFields": {
                "scene": {"$arrayElemAt": ["$scene", 0]},
                "chapter": {"$arrayElemAt": ["$chapter", 0]},
                "selected_image_id": {"$ifNull": ["$selected_image_id", None]}
            }}
        ]

        return list(self.collection.aggregate(pipeline))


# Singleton instances
chapter_repository = ChapterRepository()
scene_repository = SceneRepository()
panel_repository = PanelRepository()