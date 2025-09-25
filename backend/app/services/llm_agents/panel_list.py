"""Agent for generating panel list from scene context."""

from app.services.llm_agents.base import BaseAgent, AgentType, AgentConfig
from app.services.ai.base import LLMModel
from app.schemas.schemas import PanelList


class PanelListAgent(BaseAgent[PanelList]):
    """Generates list of panels for a specific scene."""

    agent_type = AgentType.PANEL_LIST
    name = "Panel List Generator"
    output_schema = PanelList

    config = AgentConfig(model=LLMModel.GPT_5_NANO.value)

    async def build_prompt(self) -> str:
        """Build prompt from scene context."""
        scene = self.context.data.get("scene", {})
        chapter = self.context.data.get("chapter", {})
        character_list = self.context.data.get("character_list", {})
        num_panels = self.context.data.get("num_panels", 6)

        characters = character_list.get("characters", [])
        character_names = ', '.join([char['name'] for char in characters])

        template = self.load_prompt_template("panel_list.txt")
        return template.format(
            num_panels=num_panels,
            chapter_number=chapter.get('number', 1),
            chapter_title=chapter.get('title', 'Unknown'),
            scene_number=scene.get('number', 1),
            scene_title=scene.get('title', 'Unknown'),
            scene_description=scene.get('description', 'No description'),
            character_names=character_names
        )