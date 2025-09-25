"""Agent for creating project summary from user input."""

from app.services.llm_agents.base import BaseAgent, AgentType, AgentConfig
from app.services.ai.base import LLMModel
from app.schemas.schemas import ProjectSummary


class ProjectSummaryAgent(BaseAgent[ProjectSummary]):
    """Creates a structured project summary from user's story idea."""

    agent_type = AgentType.PROJECT_SUMMARY
    name = "Project Summary Generator"
    output_schema = ProjectSummary

    # Use GPT-4o for creative interpretation with structured output
    config = AgentConfig(model=LLMModel.GPT_5_NANO.value)

    async def build_prompt(self) -> str:
        """Build prompt from user input."""
        user_input = self.context.data.get("user_input", "")

        template = self.load_prompt_template("project_summary.txt")
        return template.format(user_input=user_input)