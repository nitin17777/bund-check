"""
Structural Integrity Verification Engine.

Splits source and target into paragraphs and checks:
  - Paragraph count match (WARN on mismatch)
  - Paragraph merging or splitting
  - Empty paragraph detection
"""

import re
from typing import List, Tuple, Optional

from backend.app.models.verification import VerificationFinding, StructureAuditResult


def _split_paragraphs(text: str) -> List[str]:
    """Split text into non-empty paragraphs on blank lines."""
    raw = re.split(r"\n{2,}", text)
    return [p.strip() for p in raw if p.strip()]


def audit_structure_integrity(
    source_text: str,
    target_text: str,
    paragraph_index: Optional[int] = None,
) -> Tuple[StructureAuditResult, List[VerificationFinding]]:
    """
    Compares paragraph structure between source and target texts.

    Returns:
        (StructureAuditResult, List[VerificationFinding])
    """
    source_paras = _split_paragraphs(source_text)
    target_paras = _split_paragraphs(target_text)

    source_count = len(source_paras)
    target_count = len(target_paras)

    findings: List[VerificationFinding] = []

    if source_count == 0 and target_count == 0:
        result = StructureAuditResult(
            passed=True,
            source_count=0,
            target_count=0,
            status="ALIGNED",
        )
        return result, findings

    if source_count == target_count:
        status = "ALIGNED"
        passed = True
    else:
        passed = False
        # Determine if merge/split is likely
        if target_count < source_count:
            status = "PARAGRAPHS_MERGED_OR_SPLIT"
            msg = (
                f"Target has fewer paragraphs ({target_count}) than source ({source_count}). "
                "Paragraphs may have been merged or deleted."
            )
        else:
            status = "PARAGRAPHS_MERGED_OR_SPLIT"
            msg = (
                f"Target has more paragraphs ({target_count}) than source ({source_count}). "
                "Paragraphs may have been split or new ones added."
            )

        findings.append(
            VerificationFinding(
                category="structure",
                severity="WARN",
                code="PARAGRAPH_COUNT_MISMATCH",
                message=msg,
                paragraph_index=paragraph_index,
                details={
                    "source_paragraph_count": source_count,
                    "target_paragraph_count": target_count,
                },
            )
        )

    # Check for empty paragraphs in target
    for i, para in enumerate(target_paras):
        if not para.strip():
            findings.append(
                VerificationFinding(
                    category="structure",
                    severity="WARN",
                    code="EMPTY_PARAGRAPH_IN_TARGET",
                    message=f"Target paragraph {i} is empty or whitespace-only.",
                    paragraph_index=i,
                    details={},
                )
            )

    result = StructureAuditResult(
        passed=passed,
        source_count=source_count,
        target_count=target_count,
        status=status,
    )

    return result, findings
