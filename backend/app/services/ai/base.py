from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"


class LLMModel(str, Enum):
    # OpenAI Models
    GPT_5_NANO = "gpt-5-nano"


    # Ollama Models (local)
    QWEN3 = "qwen3:latest"


class GenerationRequest(BaseModel):
    prompt: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stop_sequences: Optional[List[str]] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    response_format: Optional[str] = None  # "text" or "json"


class GenerationResponse(BaseModel):
    text: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stop_sequences: Optional[List[str]] = None
    model: Optional[str] = None
    response_format: Optional[str] = None


class BaseLLMService(ABC):
    """Abstract base class for LLM service implementations"""

    provider: LLMProvider
    default_model: str

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text completion"""
        pass

    @abstractmethod
    async def chat(self, request: ChatRequest) -> GenerationResponse:
        """Generate chat completion"""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        request: GenerationRequest,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured output conforming to a schema"""
        pass

    @abstractmethod
    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count tokens in text for the specified model"""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models for this provider"""
        pass

    async def health_check(self) -> bool:
        """Check if the service is available"""
        try:
            # Try a minimal request
            request = GenerationRequest(
                prompt="test",
                max_tokens=1,
                temperature=0
            )
            await self.generate(request)
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.provider}: {str(e)}")
            return False

    def prepare_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        examples: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Prepare prompt with system instructions and examples"""
        full_prompt = ""

        if system_prompt:
            full_prompt += f"System: {system_prompt}\n\n"

        if examples:
            for example in examples:
                full_prompt += f"User: {example.get('user', '')}\n"
                full_prompt += f"Assistant: {example.get('assistant', '')}\n\n"

        full_prompt += f"User: {prompt}\nAssistant:"

        return full_prompt

    def convert_to_chat_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> List[ChatMessage]:
        """Convert a text prompt to chat messages format"""
        messages = []

        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))

        messages.append(ChatMessage(role="user", content=prompt))

        return messages

    def validate_request(self, request: Union[GenerationRequest, ChatRequest]) -> None:
        """Validate request parameters"""
        if isinstance(request, GenerationRequest):
            if not request.prompt:
                raise ValueError("Prompt cannot be empty")

            if request.max_tokens and request.max_tokens > 4096:
                logger.warning("Max tokens exceeds 4096, may be truncated by provider")

        elif isinstance(request, ChatRequest):
            if not request.messages:
                raise ValueError("Messages cannot be empty")

            if len(request.messages) > 100:
                logger.warning("Large number of messages may exceed context window")

    async def retry_with_backoff(
        self,
        func,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ):
        """Retry a function with exponential backoff"""
        import asyncio

        last_error = None
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2

        raise last_error


class LLMError(Exception):
    """Base exception for LLM service errors"""
    pass


class RateLimitError(LLMError):
    """Rate limit exceeded"""
    pass


class TokenLimitError(LLMError):
    """Token limit exceeded"""
    pass


class ModelNotFoundError(LLMError):
    """Model not found or not available"""
    pass


class AuthenticationError(LLMError):
    """Authentication failed"""
    pass