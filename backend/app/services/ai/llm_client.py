from typing import Dict, Any, Optional, Union
import logging

from app.services.ai.base import (
    BaseLLMService,
    LLMProvider,
    GenerationRequest,
    GenerationResponse,
    ChatRequest
)
from app.services.ai.openai_service import OpenAIService
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified client for multiple LLM providers"""

    def __init__(self, default_provider: Optional[LLMProvider] = None):
        self.default_provider = default_provider or LLMProvider.OPENAI
        self.services: Dict[LLMProvider, BaseLLMService] = {}

        # Initialize available services
        self._initialize_services()

    def _initialize_services(self):
        """Initialize available LLM services based on configuration"""

        # OpenAI
        if settings.OPENAI_API_KEY:
            self.services[LLMProvider.OPENAI] = OpenAIService(
                api_key=settings.OPENAI_API_KEY
            )
            logger.info("Initialized OpenAI service")

        # Add Anthropic when API key is available
        # if settings.ANTHROPIC_API_KEY:
        #     self.services[LLMProvider.ANTHROPIC] = AnthropicService(
        #         api_key=settings.ANTHROPIC_API_KEY
        #     )

        # Add Ollama for local models
        # if settings.OLLAMA_BASE_URL:
        #     self.services[LLMProvider.OLLAMA] = OllamaService(
        #         base_url=settings.OLLAMA_BASE_URL
        #     )

        if not self.services:
            logger.warning("No LLM services initialized. Check API keys in configuration.")

    def get_service(self, provider: Optional[LLMProvider] = None) -> BaseLLMService:
        """Get service for specified provider"""
        provider = provider or self.default_provider

        if provider not in self.services:
            available = list(self.services.keys())
            if available:
                logger.warning(f"Provider {provider} not available, using {available[0]}")
                return self.services[available[0]]
            else:
                raise ValueError("No LLM services available")

        return self.services[provider]

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        """Generate text using specified or default provider"""
        service = self.get_service(provider)

        request = GenerationRequest(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            **kwargs
        )

        response = await service.generate(request)
        return response.text

    async def chat(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        """Chat completion using specified or default provider"""
        service = self.get_service(provider)

        # Convert messages to ChatMessage objects if needed
        from app.services.ai.base import ChatMessage
        chat_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                chat_messages.append(ChatMessage(**msg))
            else:
                chat_messages.append(msg)

        request = ChatRequest(
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            **kwargs
        )

        response = await service.chat(request)
        return response.text

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.7,
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured output"""
        service = self.get_service(provider)

        request = GenerationRequest(
            prompt=prompt,
            temperature=temperature,
            model=model,
            **kwargs
        )

        return await service.generate_structured(request, schema)

    async def count_tokens(
        self,
        text: str,
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None
    ) -> int:
        """Count tokens for text"""
        service = self.get_service(provider)
        return await service.count_tokens(text, model)

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all available services"""
        results = {}
        for provider, service in self.services.items():
            try:
                results[provider.value] = await service.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {provider}: {str(e)}")
                results[provider.value] = False
        return results

    def list_providers(self) -> list:
        """List available providers"""
        return [p.value for p in self.services.keys()]

    async def list_models(self, provider: Optional[LLMProvider] = None) -> list:
        """List available models for a provider"""
        service = self.get_service(provider)
        return await service.list_models()


# Singleton instance
_llm_client = None


def get_llm_client() -> LLMClient:
    """Get or create the singleton LLM client"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client