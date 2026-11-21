"""
POST /api/v1/verify

Runs all verification checks on a (source, target) text pair and returns a
VerificationReport with structured findings and per-paragraph breakdown.
"""

import logging
from fastapi import APIRouter, Request

from backend.app.core.errors import ErrorEnvelope
from backend.app.core.security import get_limiter
from backend.app.models.verification import VerifyRequest, VerificationReport
from backend.app.services.verification.aggregate import run_full_verification

logger = logging.getLogger(__name__)
limiter = get_limiter()
router = APIRouter(tags=["verification"])


@router.post("/verify", response_model=VerificationReport, responses={429: {"model": ErrorEnvelope}})
@limiter.limit("30/minute")
async def verify_revision(request: Request, payload: VerifyRequest) -> VerificationReport:
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
        len(payload.source_text),
        len(payload.target_text),
        payload.enable_nli,
    )

    report = run_full_verification(
        source_text=payload.source_text,
        target_text=payload.target_text,
        enable_nli=payload.enable_nli,
    )

    return report
