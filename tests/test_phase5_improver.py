"""
Unit and Integration Tests for Phase 5 (Writing Improver):
- Abstract LLMProvider interface & factory
- Protected span masking and unmasking on tricky inputs (nested parens, numbers like 3.14 or 1,000, citations next to punctuation, DOIs, URLs)
- Dropped span failure detection (HTTP 422 / PROTECTED_SPAN_DROPPED)
- Paragraph chunking and heading preservation
- Prompt template divergence across all 6 modes (natural_conversational, academic_clarity, professional, simple_readable, concise, formal)
- Test pipeline using a Fake Provider located strictly inside tests/ (never importable from production code)
- Missing API key returns clear HTTP 500 error
- Real provider test (marked and skipped when no key is set in environment)
"""

import pytest
import os
from typing import Tuple, Dict, Any
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException
from backend.app.services.improver.providers.base import LLMProvider
from backend.app.services.improver.providers.factory import get_llm_provider
from backend.app.services.improver.protected_spans import mask_protected_spans, restore_protected_spans
from backend.app.services.improver.chunking import chunk_document_for_improver
from backend.app.services.improver.prompts import get_prompt_for_mode, MODE_TEMPLATES
from backend.app.services.improver.pipeline import improve_paragraph_with_retry, align_sentences_for_review

client = TestClient(app)


# Fake Provider strictly defined in tests/ for plumbing validation
class FakeTestProvider(LLMProvider):
    def __init__(self, mode_suffix: str = "improved"):
        self.mode_suffix = mode_suffix
        self.call_count = 0

    def get_provider_name(self) -> str:
        return "fake_test_provider"

    def get_model_name(self) -> str:
        return "fake-v1"

    async def generate(self, prompt: str, system_prompt: str) -> Tuple[str, Dict[str, Any]]:
        self.call_count += 1
        # Extract the paragraph text from prompt
        lines = prompt.split("Paragraph to improve:\n")
        body = lines[-1].strip() if len(lines) > 1 else prompt
        
        # Simple transformation preserving placeholders while altering style
        words = body.split()
        if "STYLE: Concise" in system_prompt:
            transformed = f"Briefly, {body}"
        elif "STYLE: Academic" in system_prompt:
            transformed = f"Scholarly analysis indicates that {body}"
        elif "STYLE: Natural" in system_prompt:
            transformed = f"In simple terms, {body}"
        elif "STYLE: Professional" in system_prompt:
            transformed = f"From an executive perspective, {body}"
        elif "STYLE: Formal" in system_prompt:
            transformed = f"It is formally observed that {body}"
        elif "STYLE: Simple" in system_prompt:
            transformed = f"Put simply, {body}"
        else:
            transformed = f"Polished: {body}"

        return transformed, {
            "prompt_tokens": len(words) * 2,
            "completion_tokens": len(words) * 2 + 5,
            "total_tokens": len(words) * 4 + 5,
            "estimated_cost_usd": 0.00001,
        }


def test_protected_spans_tricky_inputs_round_trip():
    """Validates that tricky citations, numbers, units, DOIs, and quotes round-trip perfectly."""
    sample = (
        'According to Dr. Smith (Smith et al., 2021; Jones, 2022), the experimental yield reached 42.8% '
        'with a dosage of 1,000 mg in trial #3 (see https://doi.org/10.1038/s41586-021-00000-0). '
        'The cost was estimated at $45.50 on November 12, 2023, confirming "reproducibility was achieved".'
    )

    masked, mapping = mask_protected_spans(sample)
    assert len(mapping) >= 5
    assert "__PROTECTED_SPAN_0__" in masked

    # All placeholders are present
    for placeholder in mapping:
        assert placeholder in masked

    # Simulate model preserving all placeholders
    restored = restore_protected_spans(masked, mapping)
    assert restored == sample


def test_protected_spans_dropped_span_triggers_exception():
    """Validates that if a model drops a protected placeholder, DocumentProcessingException is raised."""
    sample = "The reaction produced 3.14 kg of material (Smith, 2020)."
    masked, mapping = mask_protected_spans(sample)
    
    # Simulate a corrupted LLM response that deleted __PROTECTED_SPAN_0__
    corrupted_llm_response = "The reaction produced some material."
    
    with pytest.raises(DocumentProcessingException) as excinfo:
        restore_protected_spans(corrupted_llm_response, mapping)
    assert excinfo.value.code == "PROTECTED_SPAN_DROPPED"


def test_all_six_modes_produce_different_prompts():
    """Verifies that all 6 modes have distinct templates and prompt outputs."""
    modes = [
        "natural_conversational",
        "academic_clarity",
        "professional",
        "simple_readable",
        "concise",
        "formal",
    ]
    prompts = set()
    for m in modes:
        p, sys_p = get_prompt_for_mode(m, "This is sample text.")
        assert m in MODE_TEMPLATES or m.replace("_", " ") in MODE_TEMPLATES or len(sys_p) > 50
        prompts.add(sys_p)

    # All 6 system prompts must be distinct
    assert len(prompts) == 6


def test_chunking_preserves_headings_and_order():
    """Verifies paragraph chunking preserves heading metadata and ordering."""
    doc_text = "# Introduction\n\nFirst paragraph of text.\n\nSecond paragraph with details."
    chunks = chunk_document_for_improver(doc_text)
    
    assert len(chunks) == 3
    assert chunks[0].is_heading is True
    assert chunks[0].text == "Introduction"
    assert chunks[1].is_heading is False
    assert chunks[1].text == "First paragraph of text."
    assert chunks[2].prev_context == "First paragraph of text"


@pytest.mark.asyncio
async def test_improver_pipeline_with_fake_provider():
    """Verifies pipeline sentence alignment, span preservation, and token accounting."""
    fake_provider = FakeTestProvider()
    paragraph = "The team measured 1,000 mg in November 12, 2023. This confirms high precision."
    
    revised, changes, usage = await improve_paragraph_with_retry(
        provider=fake_provider,
        mode="academic_clarity",
        paragraph_text=paragraph,
    )

    assert "1,000 mg" in revised
    assert "November 12, 2023" in revised
    assert len(changes) >= 1
    assert usage["total_tokens"] > 0
    assert usage["estimated_cost_usd"] > 0


def test_missing_api_key_returns_clear_error():
    """Verifies that attempting to use a hosted provider with an empty key fails clearly."""
    # Ensure key is empty
    old_key = settings.GROQ_API_KEY
    settings.GROQ_API_KEY = ""
    try:
        response = client.post("/api/v1/improve", json={"text": "Test text.", "provider": "groq"})
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "MISSING_GROQ_API_KEY"
        assert "GROQ_API_KEY" in data["error"]["message"]
    finally:
        settings.GROQ_API_KEY = old_key


def test_api_rejects_empty_and_oversized_text():
    """Tests input validation boundaries."""
    # Empty
    res_empty = client.post("/api/v1/improve", json={"text": "   "})
    assert res_empty.status_code == 400
    assert res_empty.json()["error"]["code"] == "EMPTY_INPUT_TEXT"

    # Oversized (>10,000 words)
    large_text = "word " * 10050
    res_large = client.post("/api/v1/improve", json={"text": large_text})
    assert res_large.status_code == 413
    assert res_large.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY") and not settings.GROQ_API_KEY,
    reason="Live GROQ_API_KEY not present in environment; skipping real hosted test.",
)
def test_real_hosted_provider_integration():
    """Integration test executed ONLY when a real valid API key is available."""
    res = client.post(
        "/api/v1/improve",
        json={
            "text": "The experimental group showed significant improvements in 42.8% of cases (Smith, 2020).",
            "mode": "academic_clarity",
            "provider": "groq"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["provider_used"] == "groq"
    assert len(data["paragraphs"]) > 0
    assert "42.8%" in data["paragraphs"][0]["revised_text"]
    assert "(Smith, 2020)" in data["paragraphs"][0]["revised_text"]
