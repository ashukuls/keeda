"""User repository for authentication and user management."""

from typing import Optional
from bson import ObjectId
from app.db.repositories.base import BaseRepository
from app.models import User


class UserRepository(BaseRepository[User]):
    """Repository for user operations."""

    def __init__(self):
        super().__init__(User)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.get_by_field("username", username)

    async def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        return await self.exists({"username": username})

    async def get_user_projects_count(self, user_id: str) -> int:
        """Get count of projects owned by user."""
        from app.db.database import get_collection
        projects = get_collection("projects")
        return projects.count_documents({"owner_id": ObjectId(user_id)})

    async def get_user_with_stats(self, user_id: str) -> dict:
        """Get user with statistics using aggregation."""
        pipeline = [
            {"$match": {"_id": ObjectId(user_id)}},
            # Lookup projects
            {"$lookup": {
                "from": "projects",
                "localField": "_id",
                "foreignField": "owner_id",
                "as": "projects"
            }},
            # Add project count
            {"$addFields": {
                "project_count": {"$size": "$projects"},
                "active_projects": {
                    "$size": {
                        "$filter": {
                            "input": "$projects",
                            "cond": {"$eq": ["$$this.status", "in_progress"]}
                        }
                    }
                }
            }},
            # Remove projects array from result
            {"$project": {
                "projects": 0,
                "hashed_password": 0
            }}
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else None


# Singleton instance
user_repository = UserRepository()