"""Test database connectivity and basic operations."""

import pytest
from bson import ObjectId

from app.db.database import MongoDB, get_database, get_collection
from app.models import User


class TestDatabaseConnection:
    """Test database connection and basic operations."""

    async def test_database_connection(self, test_db):
        """Test that we can connect to the database."""
        # test_db fixture already connects
        assert test_db is not None
        assert test_db.name == "keeda_test"

    async def test_ping_database(self, test_db):
        """Test database ping command."""
        result = test_db.command('ping')
        assert result['ok'] == 1

    async def test_collection_access(self, test_db):
        """Test accessing collections."""
        users_collection = get_collection("users")
        assert users_collection is not None
        assert users_collection.name == "users"

    async def test_crud_operations(self, test_db):
        """Test basic CRUD operations."""
        collection = test_db["test_collection"]

        # Create
        doc = {"name": "test", "value": 42}
        result = collection.insert_one(doc)
        assert result.inserted_id is not None

        # Read
        found = collection.find_one({"_id": result.inserted_id})
        assert found is not None
        assert found["name"] == "test"
        assert found["value"] == 42

        # Update
        collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"value": 100}}
        )
        updated = collection.find_one({"_id": result.inserted_id})
        assert updated["value"] == 100

        # Delete
        delete_result = collection.delete_one({"_id": result.inserted_id})
        assert delete_result.deleted_count == 1
        assert collection.find_one({"_id": result.inserted_id}) is None

    async def test_index_creation(self, test_db):
        """Test creating indexes."""
        collection = test_db["test_indexed"]

        # Create index
        index_name = collection.create_index([("field1", 1), ("field2", -1)])
        assert index_name is not None

        # Check indexes exist
        indexes = collection.list_indexes()
        index_list = list(indexes)
        assert len(index_list) >= 2  # _id index + our index

    async def test_aggregation_pipeline(self, test_db):
        """Test running aggregation pipeline."""
        collection = test_db["test_aggregation"]

        # Insert test data
        docs = [
            {"category": "A", "value": 10},
            {"category": "A", "value": 20},
            {"category": "B", "value": 15},
            {"category": "B", "value": 25},
        ]
        collection.insert_many(docs)

        # Run aggregation
        pipeline = [
            {"$group": {
                "_id": "$category",
                "total": {"$sum": "$value"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]

        results = list(collection.aggregate(pipeline))
        assert len(results) == 2

        # Check results
        result_dict = {r["_id"]: r for r in results}
        assert result_dict["A"]["total"] == 30
        assert result_dict["A"]["count"] == 2
        assert result_dict["B"]["total"] == 40
        assert result_dict["B"]["count"] == 2