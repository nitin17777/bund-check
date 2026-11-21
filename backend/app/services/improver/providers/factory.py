"""
Provider Factory.
Instantiates the configured or requested LLM provider.
"""

from typing import Optional
from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException
from backend.app.services.improver.providers.base import LLMProvider
from backend.app.services.improver.providers.hosted import HostedLLMProvider
from backend.app.services.improver.providers.local import LocalSmallModelProvider


def get_llm_provider(override_name: Optional[str] = None) -> LLMProvider:
    name = (override_name or settings.DEFAULT_IMPROVER_PROVIDER).lower().strip()

    if name in ["groq", "openrouter", "openai"]:
        return HostedLLMProvider(provider_type=name)
    elif name in ["local", "local_small"]:
        return LocalSmallModelProvider()
    else:
        raise DocumentProcessingException(
            status_code=400,
            code="INVALID_PROVIDER",
            message=f"Provider '{name}' is unrecognized. Valid options: groq, openrouter, openai, local_small.",
        )
