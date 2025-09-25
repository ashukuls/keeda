from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Type, Union
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime, timezone
from bson import ObjectId
from enum import Enum
import asyncio
import logging
import json

from app.models.models import Draft, Generation
from app.services.ai.base import LLMProvider, LLMModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class TaskType(str, Enum):
    SCENE_SUMMARY = "scene_summary"
    CHARACTER_PROFILE = "character_profile"
    PANEL_DESCRIPTION = "panel_description"
    DIALOGUE = "dialogue"
    CHAPTER_OUTLINE = "chapter_outline"
    VISUAL_PROMPT = "visual_prompt"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OutputMode(str, Enum):
    TEXT = "text"
    STRUCTURED = "structured"
    JSON = "json"


class AgentConfig(BaseModel):
    """Configuration for task agent behavior"""
    preferred_provider: Optional[LLMProvider] = None
    preferred_model: Optional[str] = None


class TaskParameters(BaseModel):
    num_variants: int = Field(default=1, ge=1, le=5)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4000)
    model_override: Optional[str] = None
    provider_override: Optional[LLMProvider] = None
    include_context: bool = True
    style_preset: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    output_mode: OutputMode = OutputMode.TEXT
    output_schema: Optional[Dict[str, Any]] = None
    strict_schema: bool = False


class TaskContext(BaseModel):
    project_id: str
    user_id: str
    target_entity_id: Optional[str] = None
    target_entity_type: Optional[str] = None
    additional_context: Dict[str, Any] = Field(default_factory=dict)
    instructions: Optional[List[str]] = Field(default_factory=list)


class TaskResult(BaseModel):
    success: bool
    draft_ids: List[str] = Field(default_factory=list)
    generation_id: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class BaseTask(ABC, Generic[T]):
    task_type: TaskType
    name: str
    description: str
    output_schema: Optional[Type[BaseModel]] = None
    agent_config: AgentConfig = AgentConfig()  # Default agent configuration

    def __init__(
        self,
        db_client,
        llm_client,
        context: TaskContext,
        parameters: TaskParameters = None
    ):
        self.db = db_client
        self.llm_client = llm_client
        self.context = context
        self.parameters = parameters or TaskParameters()
        self.generation_id: Optional[str] = None

    def select_model(self) -> tuple[Optional[LLMProvider], Optional[str]]:
        """Select the best model for this task based on agent config and overrides"""
        # Check for parameter overrides first
        if self.parameters.provider_override or self.parameters.model_override:
            return self.parameters.provider_override, self.parameters.model_override

        # Use agent configuration
        if self.agent_config.preferred_provider or self.agent_config.preferred_model:
            return self.agent_config.preferred_provider, self.agent_config.preferred_model

        # Return None to use defaults
        return None, None


    @abstractmethod
    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch required data from MongoDB for task execution"""
        pass

    async def build_prompt(self, data: Dict[str, Any]) -> str:
        """Construct the prompt for the LLM based on fetched data

        Default implementation uses the task's template_file or template attribute.
        Override if you need custom prompt building logic.
        """
        from app.services.llm_tasks.templates import get_template_manager
        from pathlib import Path

        # Check for template file first
        template_file = getattr(self, 'template_file', None)
        template_str = getattr(self, 'template', None)

        if template_file:
            # Load template from file
            template_path = Path(__file__).parent / "prompts" / template_file
            if not template_path.exists():
                logger.error(f"Template file not found: {template_path}")
                prompt = f"Task: {self.task_type.value}\n\nData:\n{json.dumps(data, indent=2, default=str)[:2000]}\n\nPlease process this data."
            else:
                with open(template_path, 'r') as f:
                    template_content = f.read()
                template_manager = get_template_manager()
                prompt = template_manager.render_string(template_content, **data)

        elif template_str:
            # Use inline template string
            template_manager = get_template_manager()
            prompt = template_manager.render_string(template_str, **data)

        else:
            # Fallback to a basic prompt if no template is defined
            logger.warning(f"No template defined for {self.task_type.value}, using basic prompt")
            prompt = f"Task: {self.task_type.value}\n\nData:\n{json.dumps(data, indent=2, default=str)[:2000]}\n\nPlease process this data."

        # Add any custom instructions from the context
        if self.context and self.context.instructions:
            prompt += "\n\nAdditional requirements:\n"
            for instruction in self.context.instructions:
                prompt += f"- {instruction}\n"

        return prompt

    async def build_structured_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for structured output generation"""
        base_prompt = await self.build_prompt(data)

        if self.parameters.output_mode == OutputMode.STRUCTURED and self.output_schema:
            schema_str = json.dumps(self.output_schema.schema(), indent=2)
            return f"""{base_prompt}

Please provide your response in valid JSON format that conforms to the following schema:

{schema_str}

Ensure your response is valid JSON that can be parsed directly."""

        elif self.parameters.output_mode == OutputMode.JSON and self.parameters.output_schema:
            schema_str = json.dumps(self.parameters.output_schema, indent=2)
            return f"""{base_prompt}

Please provide your response in valid JSON format that conforms to the following schema:

{schema_str}

Ensure your response is valid JSON that can be parsed directly."""

        return base_prompt

    async def parse_output(self, raw_output: str) -> T:
        """Parse and validate the LLM output based on output mode"""
        if self.parameters.output_mode in [OutputMode.STRUCTURED, OutputMode.JSON]:
            try:
                # Extract JSON from the response
                json_str = self.extract_json(raw_output)
                parsed_data = json.loads(json_str)

                # Validate against schema if provided
                if self.parameters.output_mode == OutputMode.STRUCTURED and self.output_schema:
                    return self.output_schema(**parsed_data)
                elif self.parameters.output_mode == OutputMode.JSON:
                    # For JSON mode, return as dict wrapped in a BaseModel if needed
                    return parsed_data

            except (json.JSONDecodeError, ValidationError) as e:
                if self.parameters.strict_schema:
                    raise ValueError(f"Failed to parse structured output: {str(e)}")
                else:
                    logger.warning(f"Failed to parse structured output, falling back to text: {str(e)}")
                    return await self.parse_text_output(raw_output)

        return await self.parse_text_output(raw_output)

    @abstractmethod
    async def parse_text_output(self, raw_output: str) -> T:
        """Parse text output - to be implemented by subclasses"""
        pass

    async def validate_output(self, output: T) -> bool:
        """Validate the parsed output meets quality requirements

        Default implementation always returns True.
        Override this method if custom validation is needed beyond Pydantic.
        """
        return True

    def extract_json(self, text: str) -> str:
        """Extract JSON from LLM response text"""
        # Try to find JSON block in the text
        import re

        # Look for ```json blocks first
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, text)
        if matches:
            return matches[0]

        # Look for plain JSON object or array
        json_obj_pattern = r'(\{[\s\S]*\}|\[[\s\S]*\])'
        matches = re.findall(json_obj_pattern, text)
        if matches:
            # Return the longest match (likely the complete JSON)
            return max(matches, key=len)

        # If no pattern found, assume entire text is JSON
        return text.strip()

    async def create_generation_record(self) -> str:
        """Create a generation record to track task execution"""
        generation = Generation(
            user_id=ObjectId(self.context.user_id),
            project_id=ObjectId(self.context.project_id),
            generation_type="text",  # All LLM tasks generate text
            status="queued",
            entity_type=self.context.target_entity_type,
            entity_id=ObjectId(self.context.target_entity_id) if self.context.target_entity_id else None,
            prompt=f"Task: {self.task_type.value}",  # Will be updated with actual prompt
            provider=self.agent_config.preferred_provider.value if self.agent_config.preferred_provider else None,
            model=self.agent_config.preferred_model,
            parameters={
                "temperature": self.parameters.temperature,
                "max_tokens": self.parameters.max_tokens,
                "num_variants": self.parameters.num_variants,
                "task_type": self.task_type.value,
                "priority": self.parameters.priority.value
            }
        )

        result = await self.db.generations.insert_one(generation.dict(by_alias=True))
        self.generation_id = str(result.inserted_id)
        return self.generation_id

    async def update_generation_status(
        self,
        status: str,
        error: Optional[str] = None,
        result_ids: Optional[List[str]] = None
    ):
        """Update the generation record status"""
        update_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc)
        }

        if error:
            update_data["error_message"] = error

        if result_ids:
            update_data["result_ids"] = result_ids

        if status == "completed":
            update_data["completed_at"] = datetime.now(timezone.utc)

        await self.db.generations.update_one(
            {"_id": ObjectId(self.generation_id)},
            {"$set": update_data}
        )

    async def create_drafts(self, outputs: List[T]) -> List[str]:
        """Create draft records for generated outputs"""
        draft_ids = []

        for i, output in enumerate(outputs):
            # Determine entity type and ID
            entity_type = self.context.target_entity_type or "project"
            entity_id = (
                ObjectId(self.context.target_entity_id)
                if self.context.target_entity_id
                else ObjectId(self.context.project_id)
            )

            # Get the model that was actually used
            provider, model = self.select_model()

            draft = Draft(
                project_id=ObjectId(self.context.project_id),
                entity_type=entity_type,
                entity_id=entity_id,
                content=json.dumps(output.dict()),  # Store as JSON string
                status="pending",
                llm_provider=provider.value if provider else None,
                llm_model=model,
                generation_params={
                    "variant_index": i,
                    "temperature": self.parameters.temperature,
                    "task_type": self.task_type.value
                }
            )

            result = await self.db.drafts.insert_one(draft.dict(by_alias=True))
            draft_ids.append(str(result.inserted_id))

        return draft_ids

    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        use_structured: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """Execute LLM generation with retry logic

        Args:
            prompt: The prompt to send to the LLM
            max_retries: Number of retry attempts
            use_structured: Whether to use structured output generation

        Returns:
            Either a string (text generation) or dict (structured generation)
        """
        last_error = None
        provider, model = self.select_model()

        for attempt in range(max_retries):
            try:
                if use_structured and self.output_schema:
                    # Use structured generation if available
                    response = await self.llm_client.generate_structured(
                        prompt=prompt,
                        schema=self.output_schema.model_json_schema(),
                        temperature=self.parameters.temperature,
                        model=model,
                        provider=provider
                    )
                    return response
                else:
                    # Regular text generation
                    response = await self.llm_client.generate(
                        prompt=prompt,
                        temperature=self.parameters.temperature,
                        max_tokens=self.parameters.max_tokens,
                        model=model,
                        provider=provider
                    )
                    return response

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Generation attempt {attempt + 1} failed with {provider or 'default'}/{model or 'default'}: {str(e)}"
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise Exception(f"Generation failed after {max_retries} attempts: {str(last_error)}")


    async def execute(self) -> TaskResult:
        """Main task execution flow"""
        start_time = datetime.now(timezone.utc)

        try:
            await self.create_generation_record()
            await self.update_generation_status("processing")

            data = await self.fetch_data()

            outputs = []
            for i in range(self.parameters.num_variants):
                # Determine if we should use structured generation
                use_structured = (
                    self.parameters.output_mode == OutputMode.STRUCTURED
                    and self.output_schema
                )

                # Build prompt based on mode
                if use_structured:
                    prompt = await self.build_prompt(data)
                elif self.parameters.output_mode == OutputMode.JSON:
                    prompt = await self.build_structured_prompt(data)
                else:
                    prompt = await self.build_prompt(data)

                if i > 0:
                    prompt += f"\n\n(Variant {i + 1}: Please provide a different approach)"

                # Generate with appropriate method
                raw_output = await self.generate_with_retry(
                    prompt=prompt,
                    use_structured=use_structured
                )

                # Parse output based on whether it's already structured
                if use_structured and isinstance(raw_output, dict):
                    # Already structured, create model instance directly
                    try:
                        parsed_output = self.output_schema(**raw_output)
                    except ValidationError as e:
                        logger.warning(f"Structured output validation failed: {e}")
                        if self.parameters.strict_schema:
                            raise
                        else:
                            # Fall back to text parsing
                            parsed_output = await self.parse_text_output(str(raw_output))
                else:
                    # Parse text or JSON output
                    parsed_output = await self.parse_output(raw_output)

                if await self.validate_output(parsed_output):
                    outputs.append(parsed_output)
                else:
                    logger.warning(f"Variant {i + 1} failed validation")

            if not outputs:
                raise Exception("No valid outputs generated")

            draft_ids = await self.create_drafts(outputs)

            await self.update_generation_status(
                "completed",
                result_ids=draft_ids
            )

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            return TaskResult(
                success=True,
                draft_ids=draft_ids,
                generation_id=self.generation_id,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")

            if self.generation_id:
                await self.update_generation_status(
                    "failed",
                    error=str(e)
                )

            return TaskResult(
                success=False,
                generation_id=self.generation_id,
                error=str(e),
                execution_time=(datetime.now(timezone.utc) - start_time).total_seconds()
            )