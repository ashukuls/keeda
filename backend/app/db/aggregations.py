"""MongoDB aggregation pipeline utilities for complex queries."""

from typing import Dict, List, Any, Optional
from bson import ObjectId


class AggregationBuilder:
    """Helper class to build MongoDB aggregation pipelines."""

    def __init__(self):
        self.pipeline = []

    def match(self, conditions: Dict[str, Any]) -> 'AggregationBuilder':
        """Add match stage."""
        self.pipeline.append({"$match": conditions})
        return self

    def lookup(self, from_collection: str, local_field: str, foreign_field: str,
               as_field: str) -> 'AggregationBuilder':
        """Add simple lookup stage."""
        self.pipeline.append({
            "$lookup": {
                "from": from_collection,
                "localField": local_field,
                "foreignField": foreign_field,
                "as": as_field
            }
        })
        return self

    def lookup_pipeline(self, from_collection: str, let_vars: Dict[str, str],
                       pipeline: List[Dict], as_field: str) -> 'AggregationBuilder':
        """Add lookup with pipeline stage."""
        self.pipeline.append({
            "$lookup": {
                "from": from_collection,
                "let": let_vars,
                "pipeline": pipeline,
                "as": as_field
            }
        })
        return self

    def unwind(self, path: str, preserve_null: bool = False) -> 'AggregationBuilder':
        """Add unwind stage."""
        if preserve_null:
            self.pipeline.append({
                "$unwind": {
                    "path": path,
                    "preserveNullAndEmptyArrays": True
                }
            })
        else:
            self.pipeline.append({"$unwind": path})
        return self

    def group(self, id_field: Any, fields: Dict[str, Dict]) -> 'AggregationBuilder':
        """Add group stage."""
        group_stage = {"_id": id_field}
        group_stage.update(fields)
        self.pipeline.append({"$group": group_stage})
        return self

    def sort(self, fields: List[tuple]) -> 'AggregationBuilder':
        """Add sort stage."""
        sort_dict = {}
        for field, order in fields:
            sort_dict[field] = order
        self.pipeline.append({"$sort": sort_dict})
        return self

    def limit(self, n: int) -> 'AggregationBuilder':
        """Add limit stage."""
        self.pipeline.append({"$limit": n})
        return self

    def skip(self, n: int) -> 'AggregationBuilder':
        """Add skip stage."""
        self.pipeline.append({"$skip": n})
        return self

    def add_fields(self, fields: Dict[str, Any]) -> 'AggregationBuilder':
        """Add fields stage."""
        self.pipeline.append({"$addFields": fields})
        return self

    def project(self, fields: Dict[str, Any]) -> 'AggregationBuilder':
        """Add project stage."""
        self.pipeline.append({"$project": fields})
        return self

    def build(self) -> List[Dict]:
        """Return the built pipeline."""
        return self.pipeline


# Common aggregation queries
class CommonAggregations:
    """Common aggregation queries used across the application."""

    @staticmethod
    def get_hierarchy_pipeline(project_id: str) -> List[Dict]:
        """Get complete project hierarchy pipeline."""
        return [
            {"$match": {"_id": ObjectId(project_id)}},

            # Get chapters with full hierarchy
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

                            # Get panels for each scene
                            {"$lookup": {
                                "from": "panels",
                                "let": {"scene_id": "$_id"},
                                "pipeline": [
                                    {"$match": {"$expr": {"$eq": ["$scene_id", "$$scene_id"]}}},
                                    {"$sort": {"panel_number": 1}},
                                    {"$project": {
                                        "_id": 1,
                                        "panel_number": 1,
                                        "panel_type": 1,
                                        "selected_image_id": 1
                                    }}
                                ],
                                "as": "panels"
                            }}
                        ],
                        "as": "scenes"
                    }}
                ],
                "as": "chapters"
            }}
        ]

    @staticmethod
    def get_content_stats_pipeline(project_id: str) -> List[Dict]:
        """Get content statistics for a project."""
        return [
            {"$facet": {
                "chapters": [
                    {"$match": {"project_id": ObjectId(project_id)}},
                    {"$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }}
                ],
                "scenes": [
                    {"$match": {"project_id": ObjectId(project_id)}},
                    {"$group": {
                        "_id": "$scene_type",
                        "count": {"$sum": 1}
                    }}
                ],
                "panels": [
                    {"$match": {"project_id": ObjectId(project_id)}},
                    {"$group": {
                        "_id": {
                            "type": "$panel_type",
                            "has_image": {"$ne": ["$selected_image_id", None]}
                        },
                        "count": {"$sum": 1}
                    }}
                ],
                "images": [
                    {"$match": {"project_id": ObjectId(project_id)}},
                    {"$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }}
                ]
            }}
        ]

    @staticmethod
    def get_generation_queue_pipeline(user_id: Optional[str] = None) -> List[Dict]:
        """Get generation tasks in queue."""
        pipeline = [
            {"$match": {"status": {"$in": ["queued", "processing"]}}},
        ]

        if user_id:
            pipeline[0]["$match"]["user_id"] = ObjectId(user_id)

        pipeline.extend([
            {"$sort": {"created_at": 1}},

            # Get project info
            {"$lookup": {
                "from": "projects",
                "localField": "project_id",
                "foreignField": "_id",
                "as": "project"
            }},

            {"$unwind": "$project"},

            {"$project": {
                "_id": 1,
                "generation_type": 1,
                "status": 1,
                "prompt": 1,
                "created_at": 1,
                "project_name": "$project.name"
            }}
        ])

        return pipeline

    @staticmethod
    def get_recent_activity_pipeline(project_id: str, limit: int = 20) -> List[Dict]:
        """Get recent activity for a project."""
        return [
            {"$unionWith": {
                "coll": "chapters",
                "pipeline": [
                    {"$match": {"project_id": ObjectId(project_id)}},
                    {"$project": {
                        "type": {"$literal": "chapter"},
                        "name": "$title",
                        "timestamp": "$updated_at"
                    }}
                ]
            }},
            {"$unionWith": {
                "coll": "scenes",
                "pipeline": [
                    {"$match": {"project_id": ObjectId(project_id)}},
                    {"$project": {
                        "type": {"$literal": "scene"},
                        "name": "$title",
                        "timestamp": "$updated_at"
                    }}
                ]
            }},
            {"$unionWith": {
                "coll": "images",
                "pipeline": [
                    {"$match": {"project_id": ObjectId(project_id)}},
                    {"$project": {
                        "type": {"$literal": "image"},
                        "name": {"$literal": "Image generated"},
                        "timestamp": "$created_at"
                    }}
                ]
            }},
            {"$sort": {"timestamp": -1}},
            {"$limit": limit}
        ]

    @staticmethod
    def search_content_pipeline(project_id: str, search_term: str) -> List[Dict]:
        """Search across all content in a project."""
        search_regex = {"$regex": search_term, "$options": "i"}

        return [
            {"$facet": {
                "chapters": [
                    {"$match": {
                        "project_id": ObjectId(project_id),
                        "$or": [
                            {"title": search_regex},
                            {"description": search_regex}
                        ]
                    }},
                    {"$project": {
                        "type": {"$literal": "chapter"},
                        "title": 1,
                        "description": 1,
                        "chapter_number": 1
                    }}
                ],
                "scenes": [
                    {"$match": {
                        "project_id": ObjectId(project_id),
                        "$or": [
                            {"title": search_regex},
                            {"setting": search_regex},
                            {"mood": search_regex}
                        ]
                    }},
                    {"$project": {
                        "type": {"$literal": "scene"},
                        "title": 1,
                        "setting": 1,
                        "scene_number": 1
                    }}
                ],
                "panels": [
                    {"$match": {
                        "project_id": ObjectId(project_id),
                        "$or": [
                            {"description": search_regex},
                            {"narration": search_regex},
                            {"visual_prompt": search_regex}
                        ]
                    }},
                    {"$project": {
                        "type": {"$literal": "panel"},
                        "description": 1,
                        "panel_number": 1
                    }}
                ],
                "characters": [
                    {"$match": {
                        "project_id": ObjectId(project_id),
                        "$or": [
                            {"name": search_regex},
                            {"description": search_regex},
                            {"personality": search_regex}
                        ]
                    }},
                    {"$project": {
                        "type": {"$literal": "character"},
                        "name": 1,
                        "description": 1
                    }}
                ]
            }}
        ]


# Export utility function
def build_aggregation() -> AggregationBuilder:
    """Create a new aggregation builder."""
    return AggregationBuilder()