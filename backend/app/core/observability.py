"""Observability and tracing configuration for LLM API calls."""

import time
import functools
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
import logging

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logger = logging.getLogger(__name__)

# Global tracer instance
tracer = None


def setup_tracing(
    service_name: str = "keeda-backend",
    jaeger_host: str = "localhost",
    jaeger_port: int = 4317,  # OTLP gRPC port
    enabled: bool = True
) -> None:
    """Initialize OpenTelemetry tracing with OTLP exporter for Jaeger."""
    global tracer

    if not enabled:
        logger.info("Tracing disabled")
        tracer = trace.get_tracer(__name__)
        return

    try:
        # Create resource identifying the service
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
        })

        # Create OTLP exporter for Jaeger
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{jaeger_host}:{jaeger_port}",
            insecure=True  # Use insecure connection for local development
        )

        # Create tracer provider
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

        # Set as global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        tracer = trace.get_tracer(__name__, "1.0.0")

        logger.info(f"Tracing enabled with OTLP exporter to {jaeger_host}:{jaeger_port}")

    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")
        tracer = trace.get_tracer(__name__)


def instrument_fastapi(app) -> None:
    """Instrument FastAPI app for automatic tracing."""
    try:
        FastAPIInstrumentor.instrument_fastapi_app(app)
        logger.info("FastAPI instrumentation enabled")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """Context manager for creating trace spans."""
    if tracer is None:
        yield None
        return

    with tracer.start_as_current_span(
        name,
        kind=kind,
        attributes=attributes or {}
    ) as span:
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def auto_trace_class(prefix: str = "workflow"):
    """
    Class decorator that automatically adds tracing to all public async methods.

    Args:
        prefix: Prefix for span names (e.g., "workflow", "repository")
    """
    def class_decorator(cls):
        # Get all methods of the class
        for attr_name in dir(cls):
            # Skip private methods and special methods
            if attr_name.startswith('_'):
                continue

            attr = getattr(cls, attr_name)

            # Check if it's a method and is async
            if callable(attr) and hasattr(attr, '__func__'):
                import asyncio
                if asyncio.iscoroutinefunction(attr):
                    # Wrap the method with tracing
                    setattr(cls, attr_name, trace_method(prefix)(attr.__func__))

        return cls
    return class_decorator


def trace_method(prefix: str = "method"):
    """
    Decorator to automatically trace class methods.

    Args:
        prefix: Prefix for the span name (e.g., "agent_manager", "repository")
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if tracer is None:
                return await func(self, *args, **kwargs)

            # Build span name from class and method names
            class_name = self.__class__.__name__
            method_name = func.__name__
            span_name = f"{prefix}.{class_name}.{method_name}"

            with tracer.start_as_current_span(
                span_name,
                kind=trace.SpanKind.INTERNAL
            ) as span:
                # Add basic attributes
                span.set_attribute("class", class_name)
                span.set_attribute("method", method_name)

                # Add selected kwargs as attributes (filter sensitive data)
                safe_kwargs = {
                    k: str(v) for k, v in kwargs.items()
                    if k in ["project_id", "user_id", "mode", "num_characters", "num_chapters", "num_scenes", "num_panels"]
                }
                for key, value in safe_kwargs.items():
                    span.set_attribute(f"param.{key}", value)

                try:
                    result = await func(self, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            if tracer is None:
                return func(self, *args, **kwargs)

            class_name = self.__class__.__name__
            method_name = func.__name__
            span_name = f"{prefix}.{class_name}.{method_name}"

            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("class", class_name)
                span.set_attribute("method", method_name)

                try:
                    result = func(self, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def trace_llm_call(
    agent_type: Optional[str] = None,
    track_tokens: bool = True,
    track_timing: bool = True
):
    """
    Decorator for tracing LLM API calls.

    Args:
        agent_type: Type of agent making the call
        track_tokens: Whether to track token usage
        track_timing: Whether to track execution time
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if tracer is None:
                return await func(*args, **kwargs)

            # Extract context from self if available
            self = args[0] if args else None

            # Build span name
            span_name = f"llm.{agent_type or func.__name__}"

            # Initial attributes
            attributes = {
                "llm.operation": func.__name__,
            }

            if agent_type:
                attributes["llm.agent_type"] = agent_type

            # Try to extract model and provider info
            if hasattr(self, 'config'):
                if hasattr(self.config, 'model'):
                    attributes["llm.model"] = self.config.model
                if hasattr(self.config, 'provider'):
                    attributes["llm.provider"] = self.config.provider

            with tracer.start_as_current_span(
                span_name,
                kind=trace.SpanKind.CLIENT,
                attributes=attributes
            ) as span:
                try:
                    # Track timing
                    if track_timing:
                        start_time = time.time()

                    # Execute function
                    result = await func(*args, **kwargs)

                    # Track timing
                    if track_timing:
                        duration = time.time() - start_time
                        span.set_attribute("llm.duration_seconds", duration)

                    # Track tokens if available
                    if track_tokens and hasattr(result, 'usage'):
                        if result.usage:
                            span.set_attribute("llm.tokens.prompt", result.usage.prompt_tokens)
                            span.set_attribute("llm.tokens.completion", result.usage.completion_tokens)
                            span.set_attribute("llm.tokens.total", result.usage.total_tokens)

                    # Track model from response if available
                    if hasattr(result, 'model'):
                        span.set_attribute("llm.model", result.model)

                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))

                    # Add error details
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))

                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if tracer is None:
                return func(*args, **kwargs)

            # Similar logic for sync functions
            span_name = f"llm.{agent_type or func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                try:
                    if track_timing:
                        start_time = time.time()

                    result = func(*args, **kwargs)

                    if track_timing:
                        duration = time.time() - start_time
                        span.set_attribute("llm.duration_seconds", duration)

                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def add_span_attributes(attributes: Dict[str, Any]) -> None:
    """Add attributes to the current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            # Convert values to acceptable types
            if value is None:
                continue
            elif isinstance(value, (str, bool, int, float)):
                span.set_attribute(key, value)
            elif isinstance(value, (list, tuple)):
                # Convert to string representation for lists
                span.set_attribute(key, str(value))
            elif isinstance(value, dict):
                # Flatten dict or convert to string
                span.set_attribute(key, str(value))
            else:
                span.set_attribute(key, str(value))


def record_exception(exception: Exception) -> None:
    """Record an exception in the current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


class LLMMetrics:
    """Helper class for tracking LLM metrics."""

    def __init__(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.total_errors = 0
        self.model_usage = {}

    def record_request(
        self,
        model: str,
        tokens: int,
        duration: float,
        success: bool = True
    ):
        """Record metrics for an LLM request."""
        self.total_requests += 1
        self.total_tokens += tokens

        if not success:
            self.total_errors += 1

        if model not in self.model_usage:
            self.model_usage[model] = {
                "requests": 0,
                "tokens": 0,
                "errors": 0,
                "total_duration": 0
            }

        self.model_usage[model]["requests"] += 1
        self.model_usage[model]["tokens"] += tokens
        self.model_usage[model]["total_duration"] += duration

        if not success:
            self.model_usage[model]["errors"] += 1

        # Add metrics to current span
        add_span_attributes({
            "metrics.total_requests": self.total_requests,
            "metrics.total_tokens": self.total_tokens,
            "metrics.total_errors": self.total_errors,
        })

    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_errors": self.total_errors,
            "error_rate": self.total_errors / max(self.total_requests, 1),
            "model_usage": self.model_usage
        }


# Global metrics instance
llm_metrics = LLMMetrics()