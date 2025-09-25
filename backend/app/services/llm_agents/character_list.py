"""Agent for generating character list from project summary."""

from app.services.llm_agents.base import BaseAgent, AgentType, AgentConfig
from app.schemas.schemas import CharacterList


class CharacterListAgent(BaseAgent[CharacterList]):
    """Generates list of main characters for the story."""

    agent_type = AgentType.CHARACTER_LIST
    name = "Character List Generator"
    output_schema = CharacterList

    config = AgentConfig(model="gpt-4o-mini")

    async def build_prompt(self) -> str:
        """Build prompt from project context."""
        user_input = self.context.data.get("user_input", "")
        project_summary = self.context.data.get("project_summary", {})
        num_characters = self.context.data.get("num_characters", 5)

        template = self.load_prompt_template("character_list.txt")
        return template.format(
            user_input=user_input,
            num_characters=num_characters,
            title=project_summary.get('title', 'Unknown'),
            genre=project_summary.get('genre', 'Unknown'),
            description=project_summary.get('description', 'No description')
        )