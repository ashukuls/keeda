from typing import Dict, Any
from app.schemas.schemas import CharacterProfileSchema
from app.services.llm_tasks.base import BaseTask, TaskType, AgentConfig
from app.services.llm_tasks.registry import task_decorator
from app.services.ai.base import LLMProvider
import logging

logger = logging.getLogger(__name__)


@task_decorator(TaskType.CHARACTER_PROFILE)
class CharacterProfileTask(BaseTask[CharacterProfileSchema]):
    """Task for generating detailed character profiles

    This agent prefers more creative models with higher temperature
    for rich character development.
    """

    task_type = TaskType.CHARACTER_PROFILE
    name = "Character Profile Generation"
    description = "Generate comprehensive character profiles for graphic novel characters"
    output_schema = CharacterProfileSchema
    template_file = "character_profile.jinja2"

    # Agent configuration - prefer more powerful models for creative writing
    agent_config = AgentConfig(
        preferred_provider=LLMProvider.OPENAI,
        preferred_model="gpt-4-turbo-preview"
    )

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch project data and any additional context for character creation"""
        from app.services.llm_tasks.context import ContextManager
        ctx_manager = ContextManager(self.db)

        # Get project context
        project_context = await ctx_manager.get_project_context(
            self.context.project_id
        )

        return {
            **project_context,
            # Include any additional context (character brief, requirements, etc.)
            **self.context.additional_context
        }


    async def parse_text_output(self, raw_output: str) -> CharacterProfileSchema:
        """Fallback parser - should rarely be used with structured output"""
        logger.warning(f"Using fallback text parser for character profile, output length: {len(raw_output)}")

        return CharacterProfileSchema(
            biography="Character profile generated",
            personality_traits=["Not analyzed"],
            motivations=["Not analyzed"],
            fears=["Not analyzed"],
            relationships={},
            voice_style="Not analyzed",
            character_arc="Not analyzed"
        )

