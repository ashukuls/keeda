"""Base classes for LLM agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic, Type
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum
from openai import AsyncOpenAI

from app.core.config import settings

T = TypeVar('T', bound=BaseModel)


class AgentType(str, Enum):
    """Types of agents in the system"""
    # List generation agents
    PROJECT_SUMMARY = "project_summary"
    CHARACTER_LIST = "character_list"
    CHAPTER_LIST = "chapter_list"
    SCENE_LIST = "scene_list"
    PANEL_LIST = "panel_list"

    # Detail enhancement agents
    CHARACTER_PROFILE = "character_profile"
    SCENE_SUMMARY = "scene_summary"
    VISUAL_PROMPT = "visual_prompt"


class AgentConfig(BaseModel):
    """Agent configuration"""
    model: str = "gpt-3.5-turbo"


class AgentParameters(BaseModel):
    """Runtime parameters"""
    temperature: float = 0.7


class AgentContext(BaseModel):
    """Context for agent execution"""
    project_id: str
    user_id: str
    data: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC, Generic[T]):
    """Base class for all LLM agents"""

    agent_type: AgentType
    name: str
    output_schema: Type[T]
    config: AgentConfig = AgentConfig()

    def __init__(self, context: AgentContext, parameters: AgentParameters = None):
        self.context = context
        self.parameters = parameters or AgentParameters()
        # Initialize OpenAI client once
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @abstractmethod
    async def build_prompt(self) -> str:
        """Build the prompt for the LLM"""
        pass

    def load_prompt_template(self, filename: str) -> str:
        """Load prompt template from file."""
        prompt_path = Path(__file__).parent / "prompts" / filename
        with open(prompt_path, "r") as f:
            return f.read()

    async def execute(self) -> T:
        """Execute the agent using OpenAI's structured output"""
        # Build prompt
        prompt = await self.build_prompt()

        # Use OpenAI's native structured output
        completion = await self.client.beta.chat.completions.parse(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            response_format=self.output_schema,
            temperature=self.parameters.temperature
        )

        return completion.choices[0].message.parsed