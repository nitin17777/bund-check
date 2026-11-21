"""
Abstract LLM Provider Base Interface.
All external hosted APIs and local small-model inference run through this interface.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any


class LLMProvider(ABC):
    """Abstract interface for writing improver language model backends."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the canonical name of the provider."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Returns the specific model string."""
        pass

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Executes generation.
        Returns:
            Tuple[str, Dict[str, Any]]: (generated_text, usage_info)
            where usage_info contains:
                prompt_tokens: int
                completion_tokens: int
                total_tokens: int
                estimated_cost_usd: float
        """
        pass
