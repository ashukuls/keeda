"""Simplified test for agent-based LLM task system"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm_tasks.base import BaseTask, TaskContext, TaskParameters, TaskType, OutputMode, AgentConfig
from app.services.ai.llm_client import get_llm_client
from app.services.ai.base import LLMProvider
from app.core.config import settings
from app.schemas.schemas import SceneSummarySchema
from typing import Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleSceneTask(BaseTask[SceneSummarySchema]):
    """Simplified scene summary task for testing"""

    task_type = TaskType.SCENE_SUMMARY
    name = "Test Scene Summary"
    description = "Test task for scene summaries"
    output_schema = SceneSummarySchema

    # Agent configuration - this task prefers fast, cheap models
    agent_config = AgentConfig(
        preferred_provider=LLMProvider.OPENAI,
        preferred_model="gpt-3.5-turbo"
    )

    async def fetch_data(self) -> Dict[str, Any]:
        """Return mock data"""
        return {
            "scene": {
                "title": "The Dark Alley",
                "setting": "A narrow alley at midnight",
                "mood": "Tense and mysterious",
                "description": "Our hero walks cautiously through a dark alley, hearing footsteps behind them"
            },
            "project": {
                "name": "Mystery Novel",
                "genre": "Noir Mystery"
            }
        }

    async def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build a simple prompt"""
        scene = data["scene"]
        return f"""Generate a comprehensive summary for this scene:

Title: {scene["title"]}
Setting: {scene["setting"]}
Mood: {scene["mood"]}
Description: {scene["description"]}

Please provide:
1. A detailed summary (at least 100 words)
2. Key points of action
3. Emotional tone analysis
4. Character interactions
5. Visual highlights for illustration"""

    async def parse_text_output(self, raw_output: str) -> SceneSummarySchema:
        """Simple fallback parser"""
        return SceneSummarySchema(
            summary=raw_output[:500],
            key_points=["Scene described"],
            emotional_tone="Mysterious",
            character_interactions=["Not specified"],
            visual_highlights=["Dark alley scene"]
        )


class MockDB:
    """Minimal mock database"""
    def __init__(self):
        self.generations = self
        self.drafts = self

    async def insert_one(self, doc):
        from bson import ObjectId
        class Result:
            inserted_id = ObjectId()
        return Result()

    async def update_one(self, query, update):
        return {"modified_count": 1}


async def test_agent_model_selection():
    """Test that agents select their preferred models"""

    if not settings.OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY not configured")
        return False

    # Create components
    db = MockDB()
    llm_client = get_llm_client()

    # Create task context
    context = TaskContext(
        project_id="507f1f77bcf86cd799439011",
        user_id="507f1f77bcf86cd799439012"
    )

    logger.info("=" * 60)
    logger.info("TEST 1: Agent selects its preferred model")
    logger.info("=" * 60)

    # Test with default parameters (agent should use its preferred model)
    task = SimpleSceneTask(
        db_client=db,
        llm_client=llm_client,
        context=context,
        parameters=TaskParameters(
            num_variants=1,
            temperature=0.7,
            output_mode=OutputMode.STRUCTURED
        )
    )

    provider, model = task.select_model()
    logger.info(f"Agent preferred: {provider}/{model}")
    assert model == "gpt-3.5-turbo", f"Expected gpt-3.5-turbo, got {model}"

    try:
        result = await task.execute()
        if result.success:
            logger.info("✅ Task executed successfully with preferred model")
        else:
            logger.error(f"❌ Task failed: {result.error}")
    except Exception as e:
        logger.error(f"❌ Execution error: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Override agent's model selection")
    logger.info("=" * 60)

    # Test with override
    task2 = SimpleSceneTask(
        db_client=db,
        llm_client=llm_client,
        context=context,
        parameters=TaskParameters(
            num_variants=1,
            temperature=0.7,
            output_mode=OutputMode.STRUCTURED,
            provider_override=LLMProvider.OPENAI,
            model_override="gpt-4o-mini"
        )
    )

    provider, model = task2.select_model()
    logger.info(f"Override to: {provider}/{model}")
    assert model == "gpt-4o-mini", f"Expected gpt-4o-mini, got {model}"

    try:
        result = await task2.execute()
        if result.success:
            logger.info("✅ Task executed successfully with overridden model")
        else:
            logger.error(f"❌ Task failed: {result.error}")
    except Exception as e:
        logger.error(f"❌ Execution error: {e}")

    return True


async def main():
    logger.info("\n" + "=" * 60)
    logger.info("AGENT-BASED LLM SYSTEM - SIMPLIFIED TEST")
    logger.info("=" * 60 + "\n")

    success = await test_agent_model_selection()

    if success:
        logger.info("\n✅ All tests completed")
    else:
        logger.info("\n❌ Some tests failed")


if __name__ == "__main__":
    asyncio.run(main())