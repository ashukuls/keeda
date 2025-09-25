from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone

from app.db.repositories.base import BaseRepository
from app.models.models import Draft, DraftStatus


class DraftRepository(BaseRepository[Draft]):
    """Repository for draft operations"""

    model = Draft
    collection_name = "drafts"

    async def find_by_project(
        self,
        project_id: str,
        draft_type: Optional[str] = None,
        status: Optional[DraftStatus] = None,
        limit: int = 100
    ) -> List[Draft]:
        """Find drafts by project with optional filters"""
        query = {"project_id": ObjectId(project_id)}

        if draft_type:
            query["draft_type"] = draft_type

        if status:
            query["status"] = status.value

        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(None)
        return [self.model(**item) for item in items]

    async def find_by_entity(
        self,
        entity_id: str,
        entity_type: str,
        draft_type: Optional[str] = None,
        status: Optional[DraftStatus] = None
    ) -> List[Draft]:
        """Find drafts for a specific entity (scene, panel, etc.)"""
        query = {f"{entity_type}_id": ObjectId(entity_id)}

        if draft_type:
            query["draft_type"] = draft_type

        if status:
            query["status"] = status.value

        cursor = self.collection.find(query).sort("created_at", -1)
        items = await cursor.to_list(None)
        return [self.model(**item) for item in items]

    async def find_by_generation(self, generation_id: str) -> List[Draft]:
        """Find all drafts created by a specific generation task"""
        query = {"generation_id": ObjectId(generation_id)}
        cursor = self.collection.find(query).sort("metadata.variant_index", 1)
        items = await cursor.to_list(None)
        return [self.model(**item) for item in items]

    async def update_status(
        self,
        draft_id: str,
        status: DraftStatus,
        selected_at: Optional[datetime] = None
    ) -> bool:
        """Update draft status"""
        update_data = {
            "status": status.value,
            "updated_at": datetime.now(timezone.utc)
        }

        if status == DraftStatus.SELECTED and selected_at:
            update_data["selected_at"] = selected_at

        result = await self.collection.update_one(
            {"_id": ObjectId(draft_id)},
            {"$set": update_data}
        )

        return result.modified_count > 0

    async def select_draft(self, draft_id: str) -> bool:
        """Mark a draft as selected and reject others for the same entity"""
        draft = await self.get(draft_id)
        if not draft:
            return False

        # Determine entity type and ID
        entity_type = None
        entity_id = None

        for field in ["scene_id", "panel_id", "chapter_id", "character_id"]:
            if hasattr(draft, field) and getattr(draft, field):
                entity_type = field.replace("_id", "")
                entity_id = getattr(draft, field)
                break

        if entity_type and entity_id:
            # Reject other drafts for the same entity
            await self.collection.update_many(
                {
                    f"{entity_type}_id": entity_id,
                    "draft_type": draft.draft_type,
                    "_id": {"$ne": ObjectId(draft_id)},
                    "status": DraftStatus.PENDING.value
                },
                {
                    "$set": {
                        "status": DraftStatus.REJECTED.value,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

        # Select this draft
        return await self.update_status(
            draft_id,
            DraftStatus.SELECTED,
            datetime.now(timezone.utc)
        )

    async def get_selected_draft(
        self,
        entity_id: str,
        entity_type: str,
        draft_type: str
    ) -> Optional[Draft]:
        """Get the currently selected draft for an entity"""
        query = {
            f"{entity_type}_id": ObjectId(entity_id),
            "draft_type": draft_type,
            "status": DraftStatus.SELECTED.value
        }

        item = await self.collection.find_one(query)
        return self.model(**item) if item else None

    async def count_by_status(
        self,
        project_id: str,
        status: DraftStatus
    ) -> int:
        """Count drafts by status in a project"""
        return await self.collection.count_documents({
            "project_id": ObjectId(project_id),
            "status": status.value
        })

    async def cleanup_old_drafts(
        self,
        project_id: str,
        days_old: int = 30
    ) -> int:
        """Delete old rejected drafts"""
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        result = await self.collection.delete_many({
            "project_id": ObjectId(project_id),
            "status": DraftStatus.REJECTED.value,
            "created_at": {"$lt": cutoff_date}
        })

        return result.deleted_count