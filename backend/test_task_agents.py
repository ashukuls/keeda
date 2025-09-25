"""Test script for agent-based LLM task system"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_tasks.base import TaskContext, TaskParameters, TaskType, OutputMode
from app.services.llm_tasks.executor import TaskExecutor
from app.services.ai.llm_client import get_llm_client
from app.core.config import settings
import logging

# Import tasks to trigger registration
import app.services.llm_tasks.tasks

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockDB:
    """Mock database for testing"""
    def __init__(self):
        self.projects = MockCollection()
        self.chapters = MockCollection()
        self.scenes = MockCollection()
        self.panels = MockCollection()
        self.characters = MockCollection()
        self.drafts = MockCollection()
        self.generations = MockCollection()
        self.project_instructions = MockCollection()

class MockCollection:
    """Mock collection for testing"""
    def __init__(self):
        self.data = {}

    async def find_one(self, query):
        # Return mock data based on query
        if "_id" in query:
            return {
                "_id": query["_id"],
                "name": "Test Project",
                "description": "A test graphic novel",
                "title": "Test Scene",
                "mood": "dramatic",
                "setting": "Dark alley at night"
            }
        return None

    async def find(self, query):
        # Return mock cursor
        class MockCursor:
            async def to_list(self, length):
                return []
        return MockCursor()

    async def insert_one(self, doc):
        # Return mock insert result
        from bson import ObjectId
        class MockResult:
            def __init__(self):
                self.inserted_id = ObjectId()
        return MockResult()

    async def update_one(self, query, update):
        return {"modified_count": 1}


async def test_scene_summary_agent():
    """Test the scene summary task as an agent"""
    logger.info("=" * 80)
    logger.info("Testing Scene Summary Agent")
    logger.info("=" * 80)

    # Create mock database
    db = MockDB()

    # Get LLM client
    llm_client = get_llm_client()

    # Create executor
    executor = TaskExecutor(
        db_client=db,
        llm_client=llm_client,
        max_concurrent_tasks=1
    )

    # Create task context
    context = TaskContext(
        project_id="507f1f77bcf86cd799439011",
        user_id="507f1f77bcf86cd799439012",
        target_entity_id="507f1f77bcf86cd799439013",
        target_entity_type="scene"
    )

    # Create parameters with structured output
    parameters = TaskParameters(
        num_variants=1,
        temperature=0.5,
        output_mode=OutputMode.STRUCTURED,
        strict_schema=False  # Allow fallback to text parsing
    )

    try:
        logger.info("Submitting scene summary task...")
        logger.info(f"Agent will select its own model (preferred: gpt-3.5-turbo)")

        result = await executor.execute_task(
            task_type=TaskType.SCENE_SUMMARY,
            context=context,
            parameters=parameters
        )

        if result.success:
            logger.info(f"✅ Task completed successfully!")
            logger.info(f"Generation ID: {result.generation_id}")
            logger.info(f"Created {len(result.draft_ids)} draft(s)")
            logger.info(f"Execution time: {result.execution_time:.2f}s")
        else:
            logger.error(f"❌ Task failed: {result.error}")

    except Exception as e:
        logger.error(f"❌ Error executing task: {e}")


async def test_character_profile_agent():
    """Test the character profile task as an agent"""
    logger.info("=" * 80)
    logger.info("Testing Character Profile Agent")
    logger.info("=" * 80)

    # Create mock database
    db = MockDB()

    # Get LLM client
    llm_client = get_llm_client()

    # Create executor
    executor = TaskExecutor(
        db_client=db,
        llm_client=llm_client,
        max_concurrent_tasks=1
    )

    # Create task context
    context = TaskContext(
        project_id="507f1f77bcf86cd799439011",
        user_id="507f1f77bcf86cd799439012",
        target_entity_id="507f1f77bcf86cd799439014",
        target_entity_type="character"
    )

    # Create parameters
    parameters = TaskParameters(
        num_variants=1,
        temperature=0.8,  # Higher for creativity
        output_mode=OutputMode.STRUCTURED
    )

    try:
        logger.info("Submitting character profile task...")
        logger.info(f"Agent will select its own model (preferred: gpt-4-turbo-preview)")

        result = await executor.execute_task(
            task_type=TaskType.CHARACTER_PROFILE,
            context=context,
            parameters=parameters
        )

        if result.success:
            logger.info(f"✅ Task completed successfully!")
            logger.info(f"Generation ID: {result.generation_id}")
            logger.info(f"Created {len(result.draft_ids)} draft(s)")
            logger.info(f"Execution time: {result.execution_time:.2f}s")
        else:
            logger.error(f"❌ Task failed: {result.error}")

    except Exception as e:
        logger.error(f"❌ Error executing task: {e}")


async def test_model_override():
    """Test overriding the agent's model selection"""
    logger.info("=" * 80)
    logger.info("Testing Model Override")
    logger.info("=" * 80)

    # Create mock database
    db = MockDB()

    # Get LLM client
    llm_client = get_llm_client()

    # Create executor
    executor = TaskExecutor(
        db_client=db,
        llm_client=llm_client,
        max_concurrent_tasks=1
    )

    # Create task context
    context = TaskContext(
        project_id="507f1f77bcf86cd799439011",
        user_id="507f1f77bcf86cd799439012",
        target_entity_id="507f1f77bcf86cd799439015",
        target_entity_type="panel"
    )

    # Override the model selection
    from app.services.ai.base import LLMProvider
    parameters = TaskParameters(
        num_variants=1,
        temperature=0.7,
        output_mode=OutputMode.STRUCTURED,
        provider_override=LLMProvider.OPENAI,
        model_override="gpt-4o-mini"  # Force a specific model
    )

    try:
        logger.info("Submitting visual prompt task with model override...")
        logger.info(f"Overriding to use: gpt-4o-mini")

        result = await executor.execute_task(
            task_type=TaskType.VISUAL_PROMPT,
            context=context,
            parameters=parameters
        )

        if result.success:
            logger.info(f"✅ Task completed successfully with overridden model!")
            logger.info(f"Generation ID: {result.generation_id}")
            logger.info(f"Execution time: {result.execution_time:.2f}s")
        else:
            logger.error(f"❌ Task failed: {result.error}")

    except Exception as e:
        logger.error(f"❌ Error executing task: {e}")


async def main():
    """Run all tests"""
    logger.info("\n" + "=" * 80)
    logger.info("AGENT-BASED LLM TASK SYSTEM TEST")
    logger.info("=" * 80 + "\n")

    # Check if OpenAI API key is configured
    if not settings.OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY not configured in .env file")
        logger.info("Please set OPENAI_API_KEY in backend/.env to test the system")
        return

    logger.info("✅ OpenAI API key configured")
    logger.info("\nEach task agent will select its preferred LLM model:")
    logger.info("- Scene Summary: prefers gpt-3.5-turbo (fast, cost-effective)")
    logger.info("- Character Profile: prefers gpt-4-turbo-preview (creative)")
    logger.info("- Visual Prompt: prefers gpt-4-turbo-preview (descriptive)")
    logger.info("\n")

    # Run tests
    await test_scene_summary_agent()
    logger.info("\n")

    await test_character_profile_agent()
    logger.info("\n")

    await test_model_override()

    logger.info("\n" + "=" * 80)
    logger.info("TEST SUITE COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())