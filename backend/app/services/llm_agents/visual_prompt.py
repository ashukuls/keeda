"""Agent for generating image generation prompts."""

from app.services.llm_agents.base import BaseAgent, AgentType, AgentConfig
from app.services.ai.base import LLMModel
from app.schemas.schemas import ImagePrompt


class VisualPromptAgent(BaseAgent[ImagePrompt]):
    """Generates prompts for image generation."""

    agent_type = AgentType.VISUAL_PROMPT
    name = "Visual Prompt Generator"
    output_schema = ImagePrompt

    config = AgentConfig(model=LLMModel.GPT_5_NANO.value)

    async def build_prompt(self) -> str:
        """Build prompt from panel or character context."""
        target_type = self.context.data.get("target_type", "panel")

        if target_type == "panel":
            return self._build_panel_prompt()
        elif target_type == "character":
            return self._build_character_prompt()
        elif target_type == "location":
            return self._build_location_prompt()
        else:
            return self._build_panel_prompt()

    def _build_panel_prompt(self) -> str:
        """Build prompt for panel image."""
        panel = self.context.data.get("panel", {})
        scene = self.context.data.get("scene", {})
        project_summary = self.context.data.get("project_summary", {})
        visual_style = self.context.data.get("visual_style", "comic book art")

        template = self.load_prompt_template("visual_prompt_panel.txt")
        return template.format(
            genre=project_summary.get('genre', 'Unknown'),
            visual_style=visual_style,
            scene_title=scene.get('title', 'Unknown'),
            scene_description=scene.get('description', 'No description'),
            panel_number=panel.get('number', 1),
            shot_type=panel.get('shot_type', 'medium'),
            panel_description=panel.get('description', 'No description')
        )

    def _build_character_prompt(self) -> str:
        """Build prompt for character reference sheet."""
        character = self.context.data.get("character", {})
        character_profile = self.context.data.get("character_profile", {})
        project_summary = self.context.data.get("project_summary", {})
        visual_style = self.context.data.get("visual_style", "comic book art")

        template = self.load_prompt_template("visual_prompt_character.txt")
        return template.format(
            genre=project_summary.get('genre', 'Unknown'),
            visual_style=visual_style,
            name=character.get('name', 'Unknown'),
            role=character.get('role', 'Unknown'),
            description=character.get('description', 'No description'),
            biography=character_profile.get('biography', 'No profile')
        )

    def _build_location_prompt(self) -> str:
        """Build prompt for location establishing shot."""
        location = self.context.data.get("location", {})
        project_summary = self.context.data.get("project_summary", {})
        visual_style = self.context.data.get("visual_style", "comic book art")

        # For now, use a simple template inline since we don't have a location prompt file yet
        return f"""Create an image generation prompt for a location establishing shot:

Genre: {project_summary.get('genre', 'Unknown')}
Visual Style: {visual_style}

Location: {location.get('name', 'Unknown')}
Description: {location.get('description', 'No description')}

Generate:
1. A detailed image prompt for an establishing shot that shows:
   - Wide view of the location
   - Architectural or environmental details
   - Atmosphere and mood
   - Time of day and lighting
   - Art style consistent with the genre

2. A negative prompt listing things to avoid

The prompt should create a cinematic establishing shot."""