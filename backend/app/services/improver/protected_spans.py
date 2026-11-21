"""
Protected Span Masking & Restoration Engine.
Detects and protects:
1. Citations ([1], [1, 2], [1-3], (Author, 2020), (Author et al., 2021; Jones, 2022), DOI links)
2. Factual numbers, decimals, percentages, monetary amounts ($45.50, 3.14, 1,000, 42.8%)
3. Dates & temporal anchors (November 12, 2023, 2024-05-01, Q3 2022)
4. Measurement units (kg, mg, ml, km, Hz, mmHg, mm, cm, m, s, min, h)
5. URLs, email addresses, DOIs
6. Code & inline math (`inline_code`, $math$)
7. Quoted text ("exact quote", 'exact quote')

Replaces with stable, model-resilient placeholders (e.g. `__PROTECTED_SPAN_0__`).
Restores placeholders post-transformation; fails chunk immediately if any placeholder is lost.
"""

import re
from typing import List, Tuple, Dict, Any
from backend.app.core.errors import DocumentProcessingException

# Regex Patterns for Protected Elements

# 1. Code and Inline Math
CODE_PATTERN = re.compile(r"(`[^`]+`|\$[^\$]+\$)")

# 2. URLs, Emails, and DOIs
URL_DOI_PATTERN = re.compile(
    r"(https?://[^\s<>\"]+|www\.[^\s<>\"]+|mailto:[^\s<>\"]+|10\.\d{4,9}/[-._;()/:A-Za-z0-9]+|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)"
)

# 3. Citations
# Matches bracketed: [1], [1, 2], [1-3], [14]
# Matches parenthetical: (Smith et al., 2020), (Jones, 2019; Brown, 2021)
CITATION_PATTERN = re.compile(
    r"(\[\s*\d+(?:[\s,\-–]+\d+)*\s*\]|\((?:[A-Z][A-Za-z]+(?: et al\.)?(?:,?\s*\d{4}[a-z]?)(?:;\s*)?)+\))"
)

# 4. Dates
# Matches: November 12, 2023 | 12 Nov 2023 | 2023-11-12 | Q1 2024
DATE_PATTERN = re.compile(
    r"(\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b|\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b|\bQ[1-4]\s+\d{4}\b)"
)

# 5. Numbers with units or currency or percentages
# Matches: $45.50, €100, 42.8%, 3.14 kg, 1,000 mg, 50 km, etc.
NUMBER_UNIT_PATTERN = re.compile(
    r"([$€£¥]?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*(?:%|kg|g|mg|mcg|ml|l|km|m|cm|mm|nm|Hz|kHz|MHz|GHz|mmHg|kPa|s|ms|min|h|hours|days|weeks|years))?\b)"
)

# 6. Quoted Strings
QUOTED_PATTERN = re.compile(r'("[^"\n]{2,}"|“[^”\n]{2,}”|\'[^\'\n]{2,}\')')


def mask_protected_spans(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Identifies all protected spans, replaces them with __PROTECTED_SPAN_i__,
    and returns (masked_text, mapping).
    """
    spans: List[Tuple[int, int, str]] = []

    # Priority order: Code -> URLs/DOIs -> Citations -> Dates -> Quoted -> Numbers/Units
    patterns = [
        CODE_PATTERN,
        URL_DOI_PATTERN,
        CITATION_PATTERN,
        DATE_PATTERN,
        QUOTED_PATTERN,
        NUMBER_UNIT_PATTERN,
    ]

    # Collect spans avoiding overlap
    occupied: List[Tuple[int, int]] = []

    def is_overlapping(start: int, end: int) -> bool:
        for s, e in occupied:
            if not (end <= s or start >= e):
                return True
        return False

    for pat in patterns:
        for match in pat.finditer(text):
            s, e = match.span()
            matched_text = match.group(0).strip()
            # Do not mask bare 1-2 letter common words that accidentally trigger
            if not matched_text or (len(matched_text) == 1 and matched_text.isalpha()):
                continue
            if not is_overlapping(s, e):
                occupied.append((s, e))
                spans.append((s, e, match.group(0)))

    # Sort spans by start offset
    spans.sort(key=lambda x: x[0])

    # Build masked string and dictionary
    mapping: Dict[str, str] = {}
    result_parts: List[str] = []
    last_idx = 0

    for idx, (s, e, original_val) in enumerate(spans):
        placeholder = f"__PROTECTED_SPAN_{idx}__"
        mapping[placeholder] = original_val
        result_parts.append(text[last_idx:s])
        result_parts.append(placeholder)
        last_idx = e

    result_parts.append(text[last_idx:])
    masked_text = "".join(result_parts)

    return masked_text, mapping


def restore_protected_spans(revised_text: str, mapping: Dict[str, str]) -> str:
    """
    Restores placeholders into the revised text.
    Fails the chunk if any placeholder was dropped or corrupted by the model.
    """
    missing_spans = []
    for placeholder, original_val in mapping.items():
        if placeholder not in revised_text:
            missing_spans.append(placeholder)

    if missing_spans:
        raise DocumentProcessingException(
            status_code=422,
            code="PROTECTED_SPAN_DROPPED",
            message=f"Model dropped protected spans: {missing_spans}. The chunk was safely aborted.",
        )

    restored_text = revised_text
    for placeholder, original_val in mapping.items():
        restored_text = restored_text.replace(placeholder, original_val)

    return restored_text
