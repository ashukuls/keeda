from typing import Dict, Any, List, Optional
import openai
from openai import AsyncOpenAI
import tiktoken
import json
import logging

from app.services.ai.base import (
    BaseLLMService,
    LLMProvider,
    LLMModel,
    GenerationRequest,
    GenerationResponse,
    ChatRequest,
    ChatMessage,
    RateLimitError,
    TokenLimitError,
    AuthenticationError,
    ModelNotFoundError
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenAIService(BaseLLMService):
    """OpenAI API service implementation"""

    provider = LLMProvider.OPENAI
    default_model = LLMModel.GPT_5_NANO.value

    # Model context windows
    MODEL_CONTEXT_WINDOWS = {
        LLMModel.GPT_5_NANO.value: 400000,
    }

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, config)
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.organization = config.get("organization") if config else None

        if self.organization:
            self.client.organization = self.organization

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text completion using OpenAI"""
        self.validate_request(request)

        model = request.model or self.default_model

        try:
            # Convert to chat format (OpenAI deprecated completions API)
            messages = self.convert_to_chat_messages(
                request.prompt,
                request.system_prompt
            )

            # Prepare request parameters
            params = {
                "model": model,
                "messages": [msg.dict() for msg in messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
            }

            if request.stop_sequences:
                params["stop"] = request.stop_sequences

            if request.response_format == "json":
                params["response_format"] = {"type": "json_object"}

            # Make API call
            response = await self.client.chat.completions.create(**params)

            # Extract response
            text = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None

            return GenerationResponse(
                text=text,
                model=model,
                provider=self.provider.value,
                usage=usage,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "id": response.id
                }
            )

        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {str(e)}")
            raise RateLimitError(f"Rate limit exceeded: {str(e)}")

        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")

        except openai.BadRequestError as e:
            if "maximum context length" in str(e):
                raise TokenLimitError(f"Token limit exceeded: {str(e)}")
            raise ValueError(f"Invalid request: {str(e)}")

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    async def chat(self, request: ChatRequest) -> GenerationResponse:
        """Generate chat completion using OpenAI"""
        self.validate_request(request)

        model = request.model or self.default_model

        try:
            # Prepare request parameters
            params = {
                "model": model,
                "messages": [msg.dict() for msg in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
            }

            if request.stop_sequences:
                params["stop"] = request.stop_sequences

            if request.response_format == "json":
                params["response_format"] = {"type": "json_object"}

            # Make API call
            response = await self.client.chat.completions.create(**params)

            # Extract response
            text = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None

            return GenerationResponse(
                text=text,
                model=model,
                provider=self.provider.value,
                usage=usage,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "id": response.id
                }
            )

        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {str(e)}")
            raise RateLimitError(f"Rate limit exceeded: {str(e)}")

        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")

        except openai.BadRequestError as e:
            if "maximum context length" in str(e):
                raise TokenLimitError(f"Token limit exceeded: {str(e)}")
            raise ValueError(f"Invalid request: {str(e)}")

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    async def generate_structured(
        self,
        request: GenerationRequest,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured output using OpenAI function calling"""
        model = request.model or self.default_model

        # Only certain models support function calling
        if not model.startswith(("gpt-5", "gpt-4", "gpt-3.5-turbo")):
            # Fallback to JSON mode
            request.response_format = "json"
            prompt_with_schema = f"{request.prompt}\n\nPlease respond with valid JSON conforming to this schema:\n{json.dumps(schema, indent=2)}"
            request.prompt = prompt_with_schema

            response = await self.generate(request)

            try:
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                raise ValueError(f"Invalid JSON in response: {str(e)}")

        try:
            messages = self.convert_to_chat_messages(
                request.prompt,
                request.system_prompt
            )

            # Create function definition from schema
            function_def = {
                "name": "structured_output",
                "description": "Generate structured output",
                "parameters": schema
            }

            # Make API call with function
            response = await self.client.chat.completions.create(
                model=model,
                messages=[msg.dict() for msg in messages],
                functions=[function_def],
                function_call={"name": "structured_output"},
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

            # Extract function arguments
            function_call = response.choices[0].message.function_call
            if function_call and function_call.arguments:
                return json.loads(function_call.arguments)
            else:
                raise ValueError("No function call in response")

        except Exception as e:
            logger.error(f"OpenAI structured generation error: {str(e)}")
            raise

    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count tokens in text for the specified model"""
        model = model or self.default_model

        try:
            # Get encoding for model
            if model.startswith("gpt-4"):
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif model.startswith("gpt-3.5"):
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # Default to cl100k_base encoding
                encoding = tiktoken.get_encoding("cl100k_base")

            # Count tokens
            tokens = encoding.encode(text)
            return len(tokens)

        except Exception as e:
            logger.error(f"Token counting error: {str(e)}")
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4

    async def list_models(self) -> List[str]:
        """List available OpenAI models"""
        try:
            models_response = await self.client.models.list()
            models = []

            for model in models_response.data:
                # Filter for text generation models
                if any(prefix in model.id for prefix in ["gpt-4", "gpt-3.5", "text-"]):
                    models.append(model.id)

            return sorted(models)

        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            # Return default models
            return [
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k"
            ]

    def get_context_window(self, model: str) -> int:
        """Get the context window size for a model"""
        return self.MODEL_CONTEXT_WINDOWS.get(model, 4096)