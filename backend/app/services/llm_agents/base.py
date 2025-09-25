"""Base classes for LLM agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Generic, Type, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import time

from app.core.config import settings
from app.schemas.schemas import AgentType
from app.core.observability import llm_metrics
from app.services.ai.base import LLMModel

T = TypeVar('T', bound=BaseModel)


class AgentConfig(BaseModel):
    """Agent configuration"""
    model: str = LLMModel.GPT_5_NANO.value


class AgentParameters(BaseModel):
    """Runtime parameters"""
    temperature: float = 1.0  # gpt-5-nano only supports temperature=1


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
        """Execute the agent using OpenAI's structured output with tracing"""
        # Import tracer at execution time to ensure it's initialized
        from app.core import observability
        from opentelemetry import trace

        # Get the current tracer (will be set if setup_tracing was called)
        tracer = observability.tracer

        # Use global tracer if available, otherwise no-op
        if tracer is None:
            return await self._execute_without_tracing()

        with tracer.start_as_current_span(
            f"agent.{self.agent_type.value if self.agent_type else 'unknown'}",
            kind=trace.SpanKind.CLIENT
        ) as span:
            start_time = time.time()

            # Set initial span attributes
            span.set_attribute("agent.type", self.agent_type.value if self.agent_type else "unknown")
            span.set_attribute("agent.model", self.config.model)
            span.set_attribute("agent.provider", "openai")
            span.set_attribute("agent.temperature", self.parameters.temperature)

            try:
                # Build prompt
                prompt = await self.build_prompt()
                prompt_length = len(prompt)

                span.set_attribute("agent.prompt_length", prompt_length)
                # Store full prompt in span for tracing
                span.set_attribute("agent.prompt_full", prompt)

                # Call OpenAI with nested span (using global tracer)
                with tracer.start_as_current_span(
                    "openai.chat.completions.parse",
                    kind=trace.SpanKind.CLIENT
                ) as openai_span:
                    openai_span.set_attribute("llm.model", self.config.model)
                    openai_span.set_attribute("llm.temperature", self.parameters.temperature)
                    openai_span.set_attribute("llm.provider", "openai")
                    openai_span.set_attribute("llm.prompt", prompt)

                    api_start = time.time()

                    completion = await self.client.beta.chat.completions.parse(
                        model=self.config.model,
                        messages=[{"role": "user", "content": prompt}],
                        response_format=self.output_schema,
                        temperature=self.parameters.temperature
                    )

                    api_duration = time.time() - api_start
                    openai_span.set_attribute("llm.duration_seconds", api_duration)

                    # Track token usage
                    if hasattr(completion, 'usage') and completion.usage:
                        openai_span.set_attribute("llm.tokens.prompt", completion.usage.prompt_tokens)
                        openai_span.set_attribute("llm.tokens.completion", completion.usage.completion_tokens)
                        openai_span.set_attribute("llm.tokens.total", completion.usage.total_tokens)

                        # Also set on parent span
                        span.set_attribute("tokens.prompt", completion.usage.prompt_tokens)
                        span.set_attribute("tokens.completion", completion.usage.completion_tokens)
                        span.set_attribute("tokens.total", completion.usage.total_tokens)

                    # Store the parsed response (structured output) as JSON string
                    if hasattr(completion.choices[0].message, 'parsed') and completion.choices[0].message.parsed:
                        import json
                        response_dict = completion.choices[0].message.parsed.dict() if hasattr(completion.choices[0].message.parsed, 'dict') else {}
                        openai_span.set_attribute("llm.response_structured", json.dumps(response_dict, default=str))

                    # Also store raw text if available
                    if hasattr(completion.choices[0].message, 'content') and completion.choices[0].message.content:
                        openai_span.set_attribute("llm.response_raw", completion.choices[0].message.content)

                # Track metrics
                duration = time.time() - start_time

                # Extract token usage if available
                tokens_used = 0
                if hasattr(completion, 'usage') and completion.usage:
                    tokens_used = completion.usage.total_tokens

                # Record metrics
                llm_metrics.record_request(
                    model=self.config.model,
                    tokens=tokens_used,
                    duration=duration,
                    success=True
                )

                span.set_attribute("agent.success", True)
                span.set_attribute("agent.duration_seconds", duration)

                # Store the result in the parent span too
                if completion.choices[0].message.parsed:
                    import json
                    result = completion.choices[0].message.parsed
                    result_dict = result.dict() if hasattr(result, 'dict') else {}
                    span.set_attribute("agent.response", json.dumps(result_dict, default=str))

                span.set_status(trace.Status(trace.StatusCode.OK))

                return completion.choices[0].message.parsed

            except Exception as e:
                duration = time.time() - start_time

                # Record error metrics
                llm_metrics.record_request(
                    model=self.config.model,
                    tokens=0,
                    duration=duration,
                    success=False
                )

                span.set_attribute("agent.success", False)
                span.set_attribute("agent.error", str(e))
                span.set_attribute("agent.error_type", type(e).__name__)
                span.set_attribute("agent.duration_seconds", duration)
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

                raise

    async def _execute_without_tracing(self) -> T:
        """Execute the agent without tracing (fallback)"""
        prompt = await self.build_prompt()

        completion = await self.client.beta.chat.completions.parse(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            response_format=self.output_schema,
            temperature=self.parameters.temperature
        )

        return completion.choices[0].message.parsed