from typing import Dict, Any, Optional
from app.schemas.schemas import SceneSummarySchema
from app.services.llm_tasks.base import BaseTask, TaskType, AgentConfig
from app.services.llm_tasks.registry import task_decorator
from app.services.ai.base import LLMProvider
import logging

logger = logging.getLogger(__name__)


@task_decorator(TaskType.SCENE_SUMMARY)
class SceneSummaryTask(BaseTask[SceneSummarySchema]):
    """Task for generating scene summaries

    This agent prefers fast, cost-effective models for summarization.
    Uses structured output for consistent formatting.
    """

    task_type = TaskType.SCENE_SUMMARY
    name = "Scene Summary Generation"
    description = "Generate comprehensive summaries for graphic novel scenes"
    output_schema = SceneSummarySchema
    template_file = "scene_summary.jinja2"

    # Agent configuration - prefer fast, cheaper models for summarization
    agent_config = AgentConfig(
        preferred_provider=LLMProvider.OPENAI,
        preferred_model="gpt-3.5-turbo"
    )

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch project data and any additional context for scene creation"""
        from app.services.llm_tasks.context import ContextManager
        ctx_manager = ContextManager(self.db)

        # Get project context
        project_context = await ctx_manager.get_project_context(
            self.context.project_id
        )

        # Get chapter context if provided
        chapter_context = {}
        if self.context.additional_context.get("chapter_id"):
            chapter_context = await ctx_manager.get_chapter_context(
                self.context.additional_context["chapter_id"]
            )

        return {
            **project_context,
            **chapter_context,
            # Include any additional context (scene brief, previous scenes, etc.)
            **self.context.additional_context
        }


    async def parse_text_output(self, raw_output: str) -> SceneSummarySchema:
        """Fallback parser for text output - should rarely be used"""
        # This is only called if structured output fails and strict_schema is False
        # In most cases, we'll use structured output directly from the LLM
        logger.warning("Using fallback text parser - structured output preferred")

        # Basic fallback - just put the entire output as summary
        return SceneSummarySchema(
            summary=raw_output[:1000],  # Limit to 1000 chars
            key_points=["Scene content generated"],
            emotional_tone="Not analyzed",
            character_interactions=["Not analyzed"],
            visual_highlights=["Not analyzed"]
        )

