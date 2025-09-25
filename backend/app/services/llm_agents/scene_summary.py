"""Agent for generating detailed scene summaries."""

from app.services.llm_agents.base import BaseAgent, AgentType, AgentConfig
from app.services.ai.base import LLMModel
from app.schemas.schemas import SceneSummary


class SceneSummaryAgent(BaseAgent[SceneSummary]):
    """Generates detailed scene summary."""

    agent_type = AgentType.SCENE_SUMMARY
    name = "Scene Summary Generator"
    output_schema = SceneSummary

    config = AgentConfig(model=LLMModel.GPT_5_NANO.value)

    async def build_prompt(self) -> str:
        """Build prompt from scene and panel context."""
        scene = self.context.data.get("scene", {})
        panels = self.context.data.get("panels", [])
        chapter = self.context.data.get("chapter", {})

        panel_text = "\n".join([
            f"Panel {p['number']} ({p['shot_type']}): {p['description']}"
            for p in panels
        ])

        template = self.load_prompt_template("scene_summary.txt")
        return template.format(
            chapter_number=chapter.get('number', 1),
            chapter_title=chapter.get('title', 'Unknown'),
            scene_number=scene.get('number', 1),
            scene_title=scene.get('title', 'Unknown'),
            scene_description=scene.get('description', 'No description'),
            panel_text=panel_text
        )