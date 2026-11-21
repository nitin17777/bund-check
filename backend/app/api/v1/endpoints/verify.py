"""
POST /api/v1/verify

Runs all verification checks on a (source, target) text pair and returns a
VerificationReport with structured findings and per-paragraph breakdown.
"""

import logging
from fastapi import APIRouter

from backend.app.models.verification import VerifyRequest, VerificationReport
from backend.app.services.verification.aggregate import run_full_verification

logger = logging.getLogger(__name__)
router = APIRouter(tags=["verification"])


@router.post("/verify", response_model=VerificationReport)
async def verify_revision(request: VerifyRequest) -> VerificationReport:
    """
    Verify a rewritten text against its original source.

    Runs deterministic checks (numbers, citations, entities, structure)
    plus semantic checks (negation, cosine similarity, optional NLI).

    **Known limitations** (returned in every response via similarity_note):
    - Cannot detect fabricated facts or invented numbers absent from the original.
    - Negation detection is keyword-based; misses complex/implicit negations.
    - Cosine similarity is a latent-space proxy; does not guarantee logical equivalence.
    - NLI contradiction check is optional, approximate, and may miss subtle contradictions.
    """
    logger.info(
        "Verification request: source_len=%d target_len=%d enable_nli=%s",
        len(request.source_text),
        len(request.target_text),
        request.enable_nli,
    )

    report = run_full_verification(
        source_text=request.source_text,
        target_text=request.target_text,
        enable_nli=request.enable_nli,
    )

    return report
