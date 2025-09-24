"""Base repository with CRUD operations."""

from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
import logging

from app.db.database import get_collection
from app.models.base import BaseDocument

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseDocument)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[T]):
        """Initialize repository with model."""
        self.model = model
        self.collection_name = model.Config.collection_name
        self._collection: Optional[Collection] = None

    @property
    def collection(self) -> Collection:
        """Get MongoDB collection."""
        if self._collection is None:
            self._collection = get_collection(self.collection_name)
        return self._collection

    async def create(self, obj: T) -> T:
        """Create a new document."""
        try:
            # Update timestamps
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()

            # Convert to dict and insert
            doc = obj.dict(by_alias=True, exclude_unset=True)
            result = self.collection.insert_one(doc)
            obj.id = result.inserted_id

            logger.info(f"Created {self.collection_name} document: {obj.id}")
            return obj

        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error: {e}")
            raise ValueError(f"Document with unique field already exists")
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise

    async def get(self, id: str) -> Optional[T]:
        """Get document by ID."""
        try:
            doc = self.collection.find_one({"_id": ObjectId(id)})
            if doc:
                return self.model(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting document {id}: {e}")
            return None

    async def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """Get document by field value."""
        try:
            doc = self.collection.find_one({field: value})
            if doc:
                return self.model(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting document by {field}={value}: {e}")
            return None

    async def list(
        self,
        filter: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[T]:
        """List documents with optional filtering and pagination."""
        try:
            query = filter or {}
            cursor = self.collection.find(query).skip(skip).limit(limit)

            if sort:
                cursor = cursor.sort(sort)
            else:
                cursor = cursor.sort([("created_at", -1)])

            docs = list(cursor)
            return [self.model(**doc) for doc in docs]

        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []

    async def update(self, id: str, update_data: Dict[str, Any]) -> Optional[T]:
        """Update document by ID."""
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()

            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}

            result = self.collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": update_data},
                return_document=True
            )

            if result:
                logger.info(f"Updated {self.collection_name} document: {id}")
                return self.model(**result)
            return None

        except Exception as e:
            logger.error(f"Error updating document {id}: {e}")
            raise

    async def delete(self, id: str) -> bool:
        """Delete document by ID."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(id)})
            if result.deleted_count > 0:
                logger.info(f"Deleted {self.collection_name} document: {id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting document {id}: {e}")
            return False

    async def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        """Count documents with optional filter."""
        try:
            query = filter or {}
            return self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0

    async def exists(self, filter: Dict[str, Any]) -> bool:
        """Check if document exists with given filter."""
        try:
            doc = self.collection.find_one(filter, {"_id": 1})
            return doc is not None
        except Exception as e:
            logger.error(f"Error checking existence: {e}")
            return False

    async def bulk_create(self, objects: List[T]) -> List[T]:
        """Create multiple documents."""
        try:
            if not objects:
                return []

            # Update timestamps
            now = datetime.utcnow()
            docs = []
            for obj in objects:
                obj.created_at = now
                obj.updated_at = now
                docs.append(obj.dict(by_alias=True, exclude_unset=True))

            result = self.collection.insert_many(docs)

            # Update objects with inserted IDs
            for obj, inserted_id in zip(objects, result.inserted_ids):
                obj.id = inserted_id

            logger.info(f"Bulk created {len(objects)} {self.collection_name} documents")
            return objects

        except Exception as e:
            logger.error(f"Error bulk creating documents: {e}")
            raise

    async def update_many(self, filter: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple documents."""
        try:
            # Add updated_at timestamp
            update.setdefault("$set", {})["updated_at"] = datetime.utcnow()

            result = self.collection.update_many(filter, update)
            logger.info(f"Updated {result.modified_count} {self.collection_name} documents")
            return result.modified_count

        except Exception as e:
            logger.error(f"Error updating many documents: {e}")
            return 0

    async def delete_many(self, filter: Dict[str, Any]) -> int:
        """Delete multiple documents."""
        try:
            result = self.collection.delete_many(filter)
            logger.info(f"Deleted {result.deleted_count} {self.collection_name} documents")
            return result.deleted_count

        except Exception as e:
            logger.error(f"Error deleting many documents: {e}")
            return 0