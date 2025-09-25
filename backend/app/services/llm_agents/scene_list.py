"""Agent for generating scene list from chapter context."""

from app.services.llm_agents.base import BaseAgent, AgentType, AgentConfig
from app.services.ai.base import LLMModel
from app.schemas.schemas import SceneList


class SceneListAgent(BaseAgent[SceneList]):
    """Generates list of scenes for a specific chapter."""

    agent_type = AgentType.SCENE_LIST
    name = "Scene List Generator"
    output_schema = SceneList

    config = AgentConfig(model=LLMModel.GPT_5_NANO.value)

    async def build_prompt(self) -> str:
        """Build prompt from chapter context."""
        chapter = self.context.data.get("chapter", {})
        project_summary = self.context.data.get("project_summary", {})
        character_list = self.context.data.get("character_list", {})
        num_scenes = self.context.data.get("num_scenes", 8)

        characters = character_list.get("characters", [])
        character_names = ', '.join([char['name'] for char in characters])

        template = self.load_prompt_template("scene_list.txt")
        return template.format(
            num_scenes=num_scenes,
            title=project_summary.get('title', 'Unknown'),
            genre=project_summary.get('genre', 'Unknown'),
            chapter_number=chapter.get('number', 1),
            chapter_title=chapter.get('title', 'Unknown'),
            chapter_summary=chapter.get('summary', 'No summary'),
            character_names=character_names
        )