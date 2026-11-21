"""
Verification Aggregation Engine.

Collects results from all 5 checkers and produces a final VerificationReport:
  - Overall status: FAILED if any CRITICAL finding; NEEDS_REVIEW if WARN-only; PASSED otherwise.
  - Per-paragraph verification results with needs_review flags.
  - Merged finding list sorted by severity.
"""

import re
import logging
from typing import List, Optional, Dict, Any, Tuple

from backend.app.models.verification import (
    VerificationFinding,
    VerificationReport,
    VerificationStatus,
    ParagraphVerification,
    ChecksOverview,
    NumericAuditResult,
    CitationAuditResult,
    EntityAuditResult,
    StructureAuditResult,
)
from backend.app.services.verification.numbers import audit_numeric_integrity
from backend.app.services.verification.citations import audit_citation_integrity
from backend.app.services.verification.entities import audit_entity_integrity
from backend.app.services.verification.structure import audit_structure_integrity
from backend.app.services.verification.semantic import audit_semantic_integrity

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"CRITICAL": 0, "WARN": 1, "INFO": 2}


def _determine_status(findings: List[VerificationFinding]) -> VerificationStatus:
    """Determine overall status from findings list."""
    severities = {f.severity for f in findings}
    if "CRITICAL" in severities:
        return "FAILED"
    if "WARN" in severities:
        return "NEEDS_REVIEW"
    return "PASSED"


def _split_paragraphs(text: str) -> List[str]:
    """Split on double newlines."""
    return [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]


def run_full_verification(
    source_text: str,
    target_text: str,
    enable_nli: bool = False,
) -> VerificationReport:
    """
    Run all verification checks and produce a consolidated VerificationReport.

    Args:
        source_text: Original text before rewriting.
        target_text: Rewritten text to verify.
        enable_nli: Whether to run NLI contradiction check (CPU-bound, ~1–3 s extra).

    Returns:
        VerificationReport with status, similarity score, all findings, and
        per-paragraph breakdown.

    KNOWN LIMITATIONS:
      - Cannot detect fabricated facts or invented numbers absent from the original.
      - Negation detection is keyword-based; misses complex/implicit negations.
      - Cosine similarity is a latent-space proxy; does not guarantee logical equivalence.
      - NLI is optional and approximate; subtle contradictions are frequently missed.
      - Entity detection falls back to heuristics when spaCy model is unavailable.
    """
    all_findings: List[VerificationFinding] = []

    # --- Document-level checks ---

    # 1. Numeric integrity
    numeric_result, numeric_findings = audit_numeric_integrity(source_text, target_text)
    all_findings.extend(numeric_findings)

    # 2. Citation integrity
    citation_result, citation_findings = audit_citation_integrity(source_text, target_text)
    all_findings.extend(citation_findings)

    # 3. Entity integrity
    entity_result, entity_findings = audit_entity_integrity(source_text, target_text)
    all_findings.extend(entity_findings)

    # 4. Structure integrity
    structure_result, structure_findings = audit_structure_integrity(source_text, target_text)
    all_findings.extend(structure_findings)

    # 5. Semantic integrity (document-level)
    overall_score, semantic_findings, semantic_summary = audit_semantic_integrity(
        source_text, target_text, enable_nli=enable_nli
    )
    all_findings.extend(semantic_findings)

    # --- Per-paragraph checks (1:1 alignment when counts match) ---
    source_paras = _split_paragraphs(source_text)
    target_paras = _split_paragraphs(target_text)

    paragraph_verifications: List[ParagraphVerification] = []

    if source_paras and target_paras and len(source_paras) == len(target_paras):
        for i, (src_para, tgt_para) in enumerate(zip(source_paras, target_paras)):
            para_findings: List[VerificationFinding] = []

            # Numeric
            _, pn_findings = audit_numeric_integrity(src_para, tgt_para, paragraph_index=i)
            para_findings.extend(pn_findings)

            # Citations
            _, pc_findings = audit_citation_integrity(src_para, tgt_para, paragraph_index=i)
            para_findings.extend(pc_findings)

            # Entities
            _, pe_findings = audit_entity_integrity(src_para, tgt_para, paragraph_index=i)
            para_findings.extend(pe_findings)

            # Semantic (per-paragraph)
            para_score, ps_findings, _ = audit_semantic_integrity(
                src_para, tgt_para, paragraph_index=i, enable_nli=enable_nli
            )
            para_findings.extend(ps_findings)

            # Determine per-paragraph status
            para_status = _determine_status(para_findings)
            needs_review = para_status in ("FAILED", "NEEDS_REVIEW")

            paragraph_verifications.append(
                ParagraphVerification(
                    paragraph_index=i,
                    status=para_status,
                    needs_review=needs_review,
                    similarity_score=round(para_score, 4),
                    findings=para_findings,
                )
            )

    # --- Sort findings by severity ---
    all_findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 99))

    # --- Determine overall status ---
    overall_status = _determine_status(all_findings)
    overall_needs_review = overall_status in ("FAILED", "NEEDS_REVIEW")

    # --- Build ChecksOverview ---
    checks = ChecksOverview(
        numeric_integrity=numeric_result,
        citation_integrity=citation_result,
        entity_integrity=entity_result,
        structure_integrity=structure_result,
        negation_integrity=semantic_summary.get("negation", {}),
        semantic_integrity=semantic_summary.get("similarity", {}),
        contradiction_check=semantic_summary.get("nli"),
    )

    return VerificationReport(
        status=overall_status,
        overall_similarity_score=round(overall_score, 4),
        needs_review=overall_needs_review,
        checks=checks,
        findings=all_findings,
        paragraph_verifications=paragraph_verifications,
    )
