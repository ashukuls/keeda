"""Agent for generating chapter list from project and characters."""

from app.services.llm_agents.base import BaseAgent, AgentType, AgentConfig
from app.services.ai.base import LLMModel
from app.schemas.schemas import ChapterList


class ChapterListAgent(BaseAgent[ChapterList]):
    """Generates list of chapters for the story."""

    agent_type = AgentType.CHAPTER_LIST
    name = "Chapter List Generator"
    output_schema = ChapterList

    config = AgentConfig(model=LLMModel.GPT_5_NANO.value)

    async def build_prompt(self) -> str:
        """Build prompt from project and character context."""
        project_summary = self.context.data.get("project_summary", {})
        character_list = self.context.data.get("character_list", {})
        num_chapters = self.context.data.get("num_chapters", 10)

        characters = character_list.get("characters", [])
        character_text = "\n".join([
            f"- {char['name']} ({char['role']}): {char['description']}"
            for char in characters
        ])

        template = self.load_prompt_template("chapter_list.txt")
        return template.format(
            num_chapters=num_chapters,
            title=project_summary.get('title', 'Unknown'),
            genre=project_summary.get('genre', 'Unknown'),
            description=project_summary.get('description', 'No description'),
            character_text=character_text
        )