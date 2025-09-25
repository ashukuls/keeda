from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone

from app.db.repositories.base import BaseRepository
from app.models.models import Generation, GenerationStatus


class GenerationRepository(BaseRepository[Generation]):
    """Repository for generation task operations"""

    model = Generation
    collection_name = "generations"

    async def find_by_project(
        self,
        project_id: str,
        task_type: Optional[str] = None,
        status: Optional[GenerationStatus] = None,
        limit: int = 100
    ) -> List[Generation]:
        """Find generations by project with optional filters"""
        query = {"project_id": ObjectId(project_id)}

        if task_type:
            query["task_type"] = task_type

        if status:
            query["status"] = status.value

        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(None)
        return [self.model(**item) for item in items]

    async def find_by_user(
        self,
        user_id: str,
        status: Optional[GenerationStatus] = None,
        limit: int = 50
    ) -> List[Generation]:
        """Find generations by user"""
        query = {"user_id": ObjectId(user_id)}

        if status:
            query["status"] = status.value

        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(None)
        return [self.model(**item) for item in items]

    async def find_pending(self, limit: int = 10) -> List[Generation]:
        """Find pending generation tasks"""
        query = {"status": GenerationStatus.PENDING.value}
        cursor = self.collection.find(query).sort("created_at", 1).limit(limit)
        items = await cursor.to_list(None)
        return [self.model(**item) for item in items]

    async def find_in_progress(self) -> List[Generation]:
        """Find currently running generation tasks"""
        query = {"status": GenerationStatus.IN_PROGRESS.value}
        cursor = self.collection.find(query)
        items = await cursor.to_list(None)
        return [self.model(**item) for item in items]

    async def update_status(
        self,
        generation_id: str,
        status: GenerationStatus,
        error_message: Optional[str] = None,
        result_ids: Optional[List[str]] = None
    ) -> bool:
        """Update generation status"""
        update_data = {
            "status": status.value,
            "updated_at": datetime.now(timezone.utc)
        }

        if status == GenerationStatus.COMPLETED:
            update_data["completed_at"] = datetime.now(timezone.utc)

        if error_message:
            update_data["error_message"] = error_message

        if result_ids:
            update_data["result_ids"] = result_ids

        result = await self.collection.update_one(
            {"_id": ObjectId(generation_id)},
            {"$set": update_data}
        )

        return result.modified_count > 0

    async def get_with_drafts(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """Get generation with associated drafts using aggregation"""
        pipeline = [
            {"$match": {"_id": ObjectId(generation_id)}},
            {
                "$lookup": {
                    "from": "drafts",
                    "localField": "_id",
                    "foreignField": "generation_id",
                    "as": "drafts"
                }
            }
        ]

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(None)

        if results:
            generation_data = results[0]
            generation = self.model(**generation_data)
            return {
                "generation": generation,
                "drafts": generation_data.get("drafts", [])
            }

        return None

    async def count_by_status(
        self,
        project_id: str,
        status: GenerationStatus
    ) -> int:
        """Count generations by status in a project"""
        return await self.collection.count_documents({
            "project_id": ObjectId(project_id),
            "status": status.value
        })

    async def get_statistics(
        self,
        project_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get generation statistics for a project"""
        match_query = {"project_id": ObjectId(project_id)}

        if start_date:
            match_query["created_at"] = {"$gte": start_date}

        if end_date:
            if "created_at" in match_query:
                match_query["created_at"]["$lte"] = end_date
            else:
                match_query["created_at"] = {"$lte": end_date}

        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": {
                        "task_type": "$task_type",
                        "status": "$status"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$group": {
                    "_id": "$_id.task_type",
                    "statuses": {
                        "$push": {
                            "status": "$_id.status",
                            "count": "$count"
                        }
                    },
                    "total": {"$sum": "$count"}
                }
            }
        ]

        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(None)

        statistics = {}
        for result in results:
            task_type = result["_id"]
            statistics[task_type] = {
                "total": result["total"],
                "by_status": {
                    item["status"]: item["count"]
                    for item in result["statuses"]
                }
            }

        return statistics

    async def cleanup_old_failed(
        self,
        project_id: str,
        days_old: int = 7
    ) -> int:
        """Clean up old failed generation records"""
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        result = await self.collection.delete_many({
            "project_id": ObjectId(project_id),
            "status": GenerationStatus.FAILED.value,
            "created_at": {"$lt": cutoff_date}
        })

        return result.deleted_count

    async def retry_failed(self, generation_id: str) -> bool:
        """Reset a failed generation to pending for retry"""
        result = await self.collection.update_one(
            {
                "_id": ObjectId(generation_id),
                "status": GenerationStatus.FAILED.value
            },
            {
                "$set": {
                    "status": GenerationStatus.PENDING.value,
                    "updated_at": datetime.now(timezone.utc),
                    "error_message": None
                },
                "$inc": {"retry_count": 1}
            }
        )

        return result.modified_count > 0