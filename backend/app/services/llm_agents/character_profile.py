"""Agent for generating detailed character profiles."""

from app.services.llm_agents.base import BaseAgent, AgentType, AgentConfig
from app.services.ai.base import LLMModel
from app.schemas.schemas import CharacterProfile


class CharacterProfileAgent(BaseAgent[CharacterProfile]):
    """Generates detailed character profile."""

    agent_type = AgentType.CHARACTER_PROFILE
    name = "Character Profile Generator"
    output_schema = CharacterProfile

    config = AgentConfig(model=LLMModel.GPT_5_NANO.value)

    async def build_prompt(self) -> str:
        """Build prompt from character context."""
        character = self.context.data.get("character", {})
        project_summary = self.context.data.get("project_summary", {})
        character_list = self.context.data.get("character_list", {})

        other_characters = [
            char['name'] for char in character_list.get("characters", [])
            if char['name'] != character.get('name')
        ]

        template = self.load_prompt_template("character_profile.txt")
        return template.format(
            name=character.get('name', 'Unknown'),
            role=character.get('role', 'Unknown'),
            description=character.get('description', 'No description'),
            title=project_summary.get('title', 'Unknown'),
            genre=project_summary.get('genre', 'Unknown'),
            story_description=project_summary.get('description', 'No description'),
            other_characters=', '.join(other_characters)
        )