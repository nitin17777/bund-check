"""
Citation Verification Engine.
Extracts citations:
- Numbered citations: [1], [1, 2], [1-3], [14]
- Author-year citations: (Smith, 2020), (Smith et al., 2021), (Jones, 2019; Brown, 2021)
- Digital Object Identifiers: doi:10.1038/... or https://doi.org/...
Verifies set preservation and flags dropped, added, or mutated citations.
"""

import re
from typing import List, Tuple, Dict, Set
from backend.app.models.verification import VerificationFinding, CitationAuditResult

CITATION_REGEX = re.compile(
    r"(\[\s*\d+(?:[\s,\-–]+\d+)*\s*\]|\((?:[A-Z][A-Za-z]+(?: et al\.)?(?:,?\s*\d{4}[a-z]?)(?:;\s*)?)+\)|(?:https?://(?:dx\.)?doi\.org/|doi:)\s*10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)"
)


def extract_citations(text: str) -> Set[str]:
    citations = set()
    for match in CITATION_REGEX.finditer(text):
        raw = match.group(0).strip()
        # Normalize whitespace inside citation
        norm = re.sub(r"\s+", " ", raw)
        citations.add(norm)
    return citations


def audit_citation_integrity(
    source_text: str, target_text: str, paragraph_index: int = None
) -> Tuple[CitationAuditResult, List[VerificationFinding]]:
    source_cites = extract_citations(source_text)
    target_cites = extract_citations(target_text)

    missing_cites = sorted(list(source_cites - target_cites))
    added_cites = sorted(list(target_cites - source_cites))

    findings: List[VerificationFinding] = []

    if missing_cites:
        findings.append(
            VerificationFinding(
                category="citations",
                severity="CRITICAL",
                code="CITATION_DROPPED",
                message=f"Original citation(s) missing or altered in rewrite: {missing_cites}",
                paragraph_index=paragraph_index,
                details={"missing": missing_cites},
            )
        )

    if added_cites:
        findings.append(
            VerificationFinding(
                category="citations",
                severity="WARN",
                code="CITATION_INTRODUCED",
                message=f"Unverified citation(s) introduced in rewrite: {added_cites}",
                paragraph_index=paragraph_index,
                details={"added": added_cites},
            )
        )

    passed = len(missing_cites) == 0

    result = CitationAuditResult(
        passed=passed,
        missing_citations=missing_cites,
        added_citations=added_cites,
    )

    return result, findings
