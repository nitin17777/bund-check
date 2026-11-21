"""
Writing Improver Pipeline.
Coordinates:
- Paragraph chunking
- Span masking & unmasking
- Provider dispatch with backoff retries
- Sentence-aligned change diffing for accept/reject review
- Graceful partial failure & usage accounting
"""

import uuid
import asyncio
import logging
import re
from typing import List, Tuple, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException
from backend.app.models.improver import (
    ImproverMode,
    ParagraphImprovement,
    SentenceChange,
    UsageAccounting,
    ImproveResponse,
)
from backend.app.services.improver.providers.base import LLMProvider
from backend.app.services.improver.providers.factory import get_llm_provider
from backend.app.services.improver.chunking import chunk_document_for_improver
from backend.app.services.improver.protected_spans import mask_protected_spans, restore_protected_spans
from backend.app.services.improver.prompts import get_prompt_for_mode

logger = logging.getLogger(__name__)


def align_sentences_for_review(original: str, revised: str) -> List[SentenceChange]:
    """
    Sentence-level alignment between original paragraph and revised paragraph
    so the user can accept or reject individual sentence improvements.
    """
    orig_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", original) if s.strip()]
    rev_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", revised) if s.strip()]

    changes: List[SentenceChange] = []
    
    # 1-to-1 matching when sentence counts match
    if len(orig_sents) == len(rev_sents):
        for idx, (o, r) in enumerate(zip(orig_sents, rev_sents)):
            changes.append(SentenceChange(sentence_index=idx, original=o, revised=r, accepted=True))
    else:
        # If the model merged or split sentences, align greedily or provide full paragraph revision
        max_len = max(len(orig_sents), len(rev_sents))
        for idx in range(max_len):
            o = orig_sents[idx] if idx < len(orig_sents) else ""
            r = rev_sents[idx] if idx < len(rev_sents) else ""
            changes.append(SentenceChange(sentence_index=idx, original=o, revised=r, accepted=True))

    return changes


async def improve_paragraph_with_retry(
    provider: LLMProvider,
    mode: ImproverMode,
    paragraph_text: str,
    context: Optional[str] = None,
    max_retries: int = 2,
) -> Tuple[str, List[SentenceChange], Dict[str, Any]]:
    """
    Performs span masking, LLM generation, span restoration, and sentence alignment with retry.
    """
    # 1. Mask protected spans
    masked_text, span_mapping = mask_protected_spans(paragraph_text)

    # 2. Prepare prompt
    prompt, system_prompt = get_prompt_for_mode(mode, masked_text, context=context)

    # 3. Call LLM with retries
    last_err: Optional[Exception] = None
    accumulated_usage: Dict[str, Any] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    for attempt in range(max_retries + 1):
        try:
            raw_revised, usage = await provider.generate(prompt=prompt, system_prompt=system_prompt)
            for k in ["prompt_tokens", "completion_tokens", "total_tokens"]:
                accumulated_usage[k] += usage.get(k, 0)
            accumulated_usage["estimated_cost_usd"] += usage.get("estimated_cost_usd", 0.0)

            # 4. Restore protected spans
            restored_revised = restore_protected_spans(raw_revised, span_mapping)

            # 5. Sentence-aligned diffing
            changes = align_sentences_for_review(paragraph_text, restored_revised)
            return restored_revised, changes, accumulated_usage

        except Exception as e:
            last_err = e
            logger.warning("Attempt %d failed for paragraph: %s", attempt + 1, str(e))
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** attempt))

    raise last_err or RuntimeError("Paragraph improvement failed after retries.")


async def run_improver_pipeline(
    text: str,
    mode: ImproverMode = "academic_clarity",
    provider_override: Optional[str] = None,
) -> ImproveResponse:
    """
    Executes end-to-end writing improvement across paragraph chunks.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        raise DocumentProcessingException(
            status_code=400,
            code="EMPTY_INPUT_TEXT",
            message="Input text cannot be empty.",
        )

    words = len(cleaned_text.split())
    if words > settings.MAX_IMPROVE_WORD_COUNT:
        raise DocumentProcessingException(
            status_code=413,
            code="PAYLOAD_TOO_LARGE",
            message=f"Text word count ({words}) exceeds maximum limit ({settings.MAX_IMPROVE_WORD_COUNT} words).",
        )

    provider = get_llm_provider(provider_override)
    # Fail immediately if the provider is unconfigured (e.g. missing API key)
    if hasattr(provider, "api_key") and not provider.api_key:
        raise DocumentProcessingException(
            status_code=500,
            code=f"MISSING_{provider.get_provider_name().upper()}_API_KEY",
            message=(
                f"API key for hosted provider '{provider.get_provider_name()}' is not configured. "
                f"Please set {provider.get_provider_name().upper()}_API_KEY in your environment or .env file."
            ),
        )

    chunks = chunk_document_for_improver(cleaned_text)

    improved_paragraphs: List[ParagraphImprovement] = []
    total_usage = UsageAccounting()

    for chunk in chunks:
        # Preserve headings intact without model rewriting
        if chunk.is_heading:
            improved_paragraphs.append(
                ParagraphImprovement(
                    paragraph_index=chunk.chunk_index,
                    original_text=chunk.text,
                    revised_text=chunk.text,
                    is_heading=True,
                    status="SKIPPED_HEADING",
                    changes=[SentenceChange(sentence_index=0, original=chunk.text, revised=chunk.text, accepted=True)],
                )
            )
            continue

        try:
            revised_text, changes, usage = await improve_paragraph_with_retry(
                provider=provider,
                mode=mode,
                paragraph_text=chunk.text,
                context=chunk.prev_context,
                max_retries=settings.IMPROVER_MAX_RETRIES,
            )

            total_usage.prompt_tokens += usage["prompt_tokens"]
            total_usage.completion_tokens += usage["completion_tokens"]
            total_usage.total_tokens += usage["total_tokens"]
            total_usage.estimated_cost_usd += usage["estimated_cost_usd"]

            improved_paragraphs.append(
                ParagraphImprovement(
                    paragraph_index=chunk.chunk_index,
                    original_text=chunk.text,
                    revised_text=revised_text,
                    is_heading=False,
                    status="SUCCESS",
                    changes=changes,
                )
            )
        except Exception as e:
            # Graceful partial failure: keep original text and mark status FAILED
            logger.error("Failed to improve paragraph %d: %s", chunk.chunk_index, str(e))
            improved_paragraphs.append(
                ParagraphImprovement(
                    paragraph_index=chunk.chunk_index,
                    original_text=chunk.text,
                    revised_text=chunk.text,
                    is_heading=False,
                    status="FAILED",
                    changes=[SentenceChange(sentence_index=0, original=chunk.text, revised=chunk.text, accepted=False)],
                    error_message=str(e),
                )
            )

    revision_id = f"rev_{uuid.uuid4().hex[:16]}"
    total_usage.estimated_cost_usd = round(total_usage.estimated_cost_usd, 6)

    return ImproveResponse(
        revision_id=revision_id,
        mode=mode,
        provider_used=provider.get_provider_name(),
        model_used=provider.get_model_name(),
        paragraphs=improved_paragraphs,
        stats={
            "original_word_count": words,
            "paragraph_count": len(improved_paragraphs),
            "improved_paragraphs_count": sum(1 for p in improved_paragraphs if p.status == "SUCCESS"),
        },
        usage=total_usage,
    )
