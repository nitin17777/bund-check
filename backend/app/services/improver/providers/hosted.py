"""
Hosted LLM Provider (Groq, OpenRouter, OpenAI compatible).
Reads API key strictly from environment settings. Fails cleanly with HTTP 500 / 502 if key is missing or invalid.
"""

import httpx
import logging
from typing import Tuple, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException
from backend.app.services.improver.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class HostedLLMProvider(LLMProvider):
    def __init__(self, provider_type: str = "groq"):
        self.provider_type = provider_type.lower().strip()
        
        if self.provider_type == "groq":
            self.api_key = settings.GROQ_API_KEY
            self.model = settings.GROQ_MODEL
            self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
            self.cost_per_m_in = 0.59
            self.cost_per_m_out = 0.79
        elif self.provider_type == "openrouter":
            self.api_key = settings.OPENROUTER_API_KEY
            self.model = settings.OPENROUTER_MODEL
            self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
            self.cost_per_m_in = 0.50
            self.cost_per_m_out = 0.75
        elif self.provider_type == "openai":
            self.api_key = settings.OPENAI_API_KEY
            self.model = settings.OPENAI_MODEL
            self.endpoint = "https://api.openai.com/v1/chat/completions"
            self.cost_per_m_in = 0.15
            self.cost_per_m_out = 0.60
        else:
            raise DocumentProcessingException(
                status_code=400,
                code="UNSUPPORTED_HOSTED_PROVIDER",
                message=f"Hosted provider '{provider_type}' is not supported.",
            )

    def get_provider_name(self) -> str:
        return self.provider_type

    def get_model_name(self) -> str:
        return self.model

    async def generate(self, prompt: str, system_prompt: str) -> Tuple[str, Dict[str, Any]]:
        if not self.api_key:
            logger.error("Missing API key for provider: %s", self.provider_type)
            raise DocumentProcessingException(
                status_code=500,
                code=f"MISSING_{self.provider_type.upper()}_API_KEY",
                message=(
                    f"API key for hosted provider '{self.provider_type}' is not configured. "
                    f"Please set {self.provider_type.upper()}_API_KEY in your environment or .env file."
                ),
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider_type == "openrouter":
            headers["HTTP-Referer"] = "https://bundcheck.local"
            headers["X-Title"] = "BundCheck Writing Improver"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=settings.IMPROVER_TIMEOUT_SECONDS) as client:
            try:
                response = await client.post(self.endpoint, json=payload, headers=headers)
                if response.status_code != 200:
                    err_detail = response.text[:200]
                    logger.error("Provider %s error: status=%d, detail=%s", self.provider_type, response.status_code, err_detail)
                    raise DocumentProcessingException(
                        status_code=502,
                        code=f"{self.provider_type.upper()}_UPSTREAM_ERROR",
                        message=f"Upstream provider '{self.provider_type}' returned error (HTTP {response.status_code}).",
                    )
                
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"].strip()
                
                usage = res_data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", len(prompt.split()) * 2)
                completion_tokens = usage.get("completion_tokens", len(content.split()) * 2)
                total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
                
                # Accounting
                cost = (prompt_tokens / 1_000_000.0) * self.cost_per_m_in + (completion_tokens / 1_000_000.0) * self.cost_per_m_out
                
                return content, {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": round(cost, 6),
                }

            except httpx.TimeoutException:
                logger.error("Provider %s timed out after %.1f seconds", self.provider_type, settings.IMPROVER_TIMEOUT_SECONDS)
                raise DocumentProcessingException(
                    status_code=504,
                    code=f"{self.provider_type.upper()}_TIMEOUT",
                    message=f"Request to provider '{self.provider_type}' timed out.",
                )
            except DocumentProcessingException:
                raise
            except Exception as e:
                logger.exception("Failed to connect to provider %s: %s", self.provider_type, str(e))
                raise DocumentProcessingException(
                    status_code=502,
                    code=f"{self.provider_type.upper()}_CONNECTION_FAILED",
                    message=f"Could not connect to provider '{self.provider_type}': {str(e)}",
                )
