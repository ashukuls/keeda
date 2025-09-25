"""Test character creation vs enhancement scenarios"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_tasks.base import TaskContext, TaskParameters, TaskType, OutputMode
from app.services.llm_tasks.tasks.character_profile import CharacterProfileTask
from app.services.ai.llm_client import get_llm_client
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockDB:
    """Mock database for testing"""
    def __init__(self):
        self.generations = self
        self.drafts = self
        self.projects = self
        self.characters = self

    async def insert_one(self, doc):
        from bson import ObjectId
        class Result:
            inserted_id = ObjectId()
        return Result()

    async def update_one(self, query, update):
        return {"modified_count": 1}

    async def find_one(self, query):
        # Mock project data
        if "projects" in str(query):
            return {
                "_id": query.get("_id"),
                "name": "Epic Fantasy Novel",
                "genre": "Dark Fantasy",
                "description": "A tale of heroes fighting against an ancient evil"
            }
        # Mock character data
        elif "characters" in str(query):
            return {
                "_id": query.get("_id"),
                "name": "Aragorn",
                "role": "protagonist",
                "description": "A ranger who becomes king"
            }
        return None


async def test_character_creation():
    """Test creating new characters for a project"""
    logger.info("=" * 60)
    logger.info("TEST: Creating new characters for a novel")
    logger.info("=" * 60)

    if not settings.OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY not configured")
        return

    db = MockDB()
    llm_client = get_llm_client()

    # Context for creating new characters (no target_entity_id)
    context = TaskContext(
        project_id="507f1f77bcf86cd799439011",
        user_id="507f1f77bcf86cd799439012",
        target_entity_id=None,  # No existing character
        target_entity_type=None,
        additional_context={
            "character_brief": "Create a protagonist - a reluctant hero with a mysterious past",
            "num_characters": 1
        }
    )

    task = CharacterProfileTask(
        db_client=db,
        llm_client=llm_client,
        context=context,
        parameters=TaskParameters(
            num_variants=1,
            temperature=0.8,  # Higher for creativity
            output_mode=OutputMode.STRUCTURED
        )
    )

    try:
        # Check what data the task fetches
        data = await task.fetch_data()
        logger.info(f"Mode: {data.get('mode')}")
        logger.info(f"Project: {data.get('project', {}).get('name')}")
        logger.info(f"Brief: {data.get('character_brief')}")

        # Execute the task
        result = await task.execute()
        if result.success:
            logger.info("✅ Successfully created character profile")
            logger.info(f"Draft IDs: {result.draft_ids}")
        else:
            logger.error(f"❌ Failed: {result.error}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")


async def test_character_enhancement():
    """Test enhancing an existing character"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: Enhancing an existing character")
    logger.info("=" * 60)

    if not settings.OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY not configured")
        return

    db = MockDB()
    llm_client = get_llm_client()

    # Context for enhancing existing character (with target_entity_id)
    context = TaskContext(
        project_id="507f1f77bcf86cd799439011",
        user_id="507f1f77bcf86cd799439012",
        target_entity_id="507f1f77bcf86cd799439013",  # Existing character ID
        target_entity_type="character",
        additional_context={
            "instructions": ["Make the character more complex", "Add internal conflicts"]
        }
    )

    task = CharacterProfileTask(
        db_client=db,
        llm_client=llm_client,
        context=context,
        parameters=TaskParameters(
            num_variants=1,
            temperature=0.7,
            output_mode=OutputMode.STRUCTURED
        )
    )

    try:
        # Check what data the task fetches
        data = await task.fetch_data()
        logger.info(f"Mode: {data.get('mode')}")
        logger.info(f"Character: {data.get('character', {}).get('name')}")

        # Execute the task
        result = await task.execute()
        if result.success:
            logger.info("✅ Successfully enhanced character profile")
            logger.info(f"Draft IDs: {result.draft_ids}")
        else:
            logger.error(f"❌ Failed: {result.error}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")


async def main():
    logger.info("\n" + "=" * 60)
    logger.info("CHARACTER TASK - CREATION vs ENHANCEMENT")
    logger.info("=" * 60 + "\n")

    await test_character_creation()
    await test_character_enhancement()

    logger.info("\n✅ Tests completed")


if __name__ == "__main__":
    asyncio.run(main())