#!/usr/bin/env python3
"""Test MongoDB connection with the new keeda_user."""

from pymongo import MongoClient
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_connections():
    """Test both main and test database connections."""

    # Get credentials from environment
    username = os.getenv("MONGO_USERNAME", "keeda_user")
    password = os.getenv("MONGO_PASSWORD", "keeda_password_2024")
    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    auth_source = os.getenv("MONGO_AUTH_SOURCE", "admin")
    database_name = os.getenv("DATABASE_NAME", "keeda")
    test_database_name = os.getenv("TEST_DATABASE_NAME", "keeda_test")

    connections = [
        {
            "name": f"Main Database ({database_name})",
            "url": f"mongodb://{username}:{password}@{host}:{port}/{database_name}?authSource={auth_source}",
            "db_name": database_name
        },
        {
            "name": f"Test Database ({test_database_name})",
            "url": f"mongodb://{username}:{password}@{host}:{port}/{test_database_name}?authSource={auth_source}",
            "db_name": test_database_name
        }
    ]

    print("Testing MongoDB connections with keeda_user...\n")
    print("=" * 60)

    for conn in connections:
        print(f"\nTesting: {conn['name']}")
        print("-" * 40)

        try:
            # Connect
            client = MongoClient(conn['url'])
            db = client[conn['db_name']]

            # Test connection
            db.command('ping')
            print("✓ Connection successful")

            # List collections
            collections = db.list_collection_names()
            print(f"✓ Found {len(collections)} collections")
            if collections:
                print(f"  Collections: {', '.join(collections[:5])}{'...' if len(collections) > 5 else ''}")

            # Test write permission
            test_col = db['_connection_test']
            result = test_col.insert_one({"test": "data"})
            print(f"✓ Write test successful (ID: {result.inserted_id})")

            # Clean up
            test_col.delete_one({"_id": result.inserted_id})
            print("✓ Cleanup successful")

            client.close()

        except Exception as e:
            print(f"✗ Error: {e}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("All connections tested successfully!")
    print("\nYou can now use the keeda_user for your application.")


if __name__ == "__main__":
    test_connections()