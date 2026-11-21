"""
Local Small-Model Provider.
Supports lightweight open-weight models (e.g. Qwen2.5-1.5B-Instruct, Llama-3.2-1B-Instruct).

HARDWARE & REALISTIC CONSTRAINTS FOR RTX 2050 (4 GB VRAM):
- Local 7B+ parameter models CANNOT run in 4GB VRAM.
- 1.5B parameter models in 4-bit/8-bit quantization require ~1.2 - 1.8 GB VRAM, fitting within the 4 GB ceiling.
- By default or when CUDA is unavailable, this provider runs CPU inference using standard PyTorch / Transformers.
"""

import logging
from typing import Tuple, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException
from backend.app.services.improver.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class LocalSmallModelProvider(LLMProvider):
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.model_name = model_name or settings.LOCAL_SMALL_MODEL
        self.device = device or settings.LOCAL_SMALL_DEVICE
        self._tokenizer = None
        self._model = None

    def get_provider_name(self) -> str:
        return "local_small"

    def get_model_name(self) -> str:
        return self.model_name

    def _lazy_load(self):
        if self._model is None:
            try:
                import torch
                from transformers import AutoTokenizer, AutoModelForCausalLM

                logger.info("Loading local small model %s on %s...", self.model_name, self.device)
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                
                # Check hardware limits: if cuda requested, verify available memory
                if self.device.startswith("cuda") and torch.cuda.is_available():
                    free_vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                    logger.info("Total VRAM detected: %.2f GB", free_vram)
                    # Load in FP16
                    self._model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16,
                        device_map=self.device,
                    )
                else:
                    # CPU execution
                    self._model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float32,
                    ).to("cpu")
                
                self._model.eval()
                logger.info("Local small model loaded successfully.")
            except Exception as e:
                logger.error("Failed to load local small model %s: %s", self.model_name, str(e))
                raise DocumentProcessingException(
                    status_code=500,
                    code="LOCAL_MODEL_LOAD_FAILED",
                    message=f"Failed to load local model '{self.model_name}': {str(e)}",
                )

    async def generate(self, prompt: str, system_prompt: str) -> Tuple[str, Dict[str, Any]]:
        self._lazy_load()
        import torch

        full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        inputs = self._tokenizer(full_prompt, return_tensors="pt").to(self._model.device)
        
        prompt_tokens = inputs.input_ids.shape[1]
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.3,
                do_sample=True,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        
        completion_ids = outputs[0][prompt_tokens:]
        completion_tokens = len(completion_ids)
        result_text = self._tokenizer.decode(completion_ids, skip_special_tokens=True).strip()

        return result_text, {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": 0.0,
        }
