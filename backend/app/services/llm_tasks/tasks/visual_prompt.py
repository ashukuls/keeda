"""Visual Prompt Generation Task - Example of a minimal task implementation"""

from typing import Dict, Any
from app.schemas.schemas import ImagePromptSchema
from app.services.llm_tasks.base import BaseTask, TaskType, AgentConfig
from app.services.llm_tasks.registry import task_decorator
from app.services.ai.base import LLMProvider
import logging

logger = logging.getLogger(__name__)


@task_decorator(TaskType.VISUAL_PROMPT)
class VisualPromptTask(BaseTask[ImagePromptSchema]):
    """Task for generating image generation prompts from panel descriptions

    This agent specializes in creating detailed visual descriptions.
    Can use vision models if reference images are provided.
    """

    task_type = TaskType.VISUAL_PROMPT
    name = "Visual Prompt Generation"
    description = "Generate detailed image generation prompts for panels"
    output_schema = ImagePromptSchema
    template_file = "visual_prompt.jinja2"

    # Agent configuration - balanced model for descriptive writing
    agent_config = AgentConfig(
        preferred_provider=LLMProvider.OPENAI,
        preferred_model="gpt-4-turbo-preview"  # Good at visual descriptions
    )

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch project data and any additional context for visual prompt generation"""
        from app.services.llm_tasks.context import ContextManager
        ctx_manager = ContextManager(self.db)

        # Get project context for style guide
        project_context = await ctx_manager.get_project_context(
            self.context.project_id
        )

        # Get scene context if provided
        scene_context = {}
        if self.context.additional_context.get("scene_id"):
            scene_context = await ctx_manager.get_scene_context(
                self.context.additional_context["scene_id"],
                include_panels=False
            )

        return {
            **project_context,
            **scene_context,
            # Include any additional context (panel description, mood, etc.)
            **self.context.additional_context
        }

    # That's it! The base class handles:
    # - build_prompt (using default_visual_prompt template)
    # - parse_text_output (fallback)
    # - validate_output (always returns True)
    # - Everything else!

    async def parse_text_output(self, raw_output: str) -> ImagePromptSchema:
        """Simple fallback parser"""
        return ImagePromptSchema(
            prompt=raw_output[:500],
            negative_prompt=None,
            style=None
        )