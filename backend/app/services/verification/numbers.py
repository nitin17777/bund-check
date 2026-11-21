"""
Numeric, Date, Percentage, and Unit Verification Engine.
Extracts and normalizes:
- Factual numbers (integers, floats, comma-separated e.g. "1,000" vs "1000")
- Dates (e.g. "November 12, 2023", "2023-11-12")
- Percentages (e.g. "42.8%", "15 percent")
- Currency amounts (e.g. "$45.50", "€100")
- Units (e.g. "10 kg", "500 mg", "30 ml")
Reports added, removed, and mutated numerical entities.
"""

import re
from typing import List, Tuple, Dict, Set, Any
from backend.app.models.verification import VerificationFinding, NumericAuditResult


def normalize_number_string(val_str: str) -> str:
    """Normalizes numbers like 1,000 to 1000, 42.0 to 42, etc."""
    cleaned = val_str.replace(",", "").strip()
    try:
        f = float(cleaned)
        if f.is_integer():
            return str(int(f))
        return f"{f:.4g}"
    except ValueError:
        return cleaned.lower()


NUM_UNIT_REGEX = re.compile(
    r"([$€£¥]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:\s*(?:%|percent|kg|g|mg|mcg|ml|l|km|m|cm|mm|nm|Hz|kHz|MHz|GHz|mmHg|kPa|s|ms|min|h|hours|days|weeks|years))?(?=\s|$|[.,;:!?)]))"
)

DATE_REGEX = re.compile(
    r"(\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b|\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b|\bQ[1-4]\s+\d{4}\b)"
)


def extract_numeric_entities(text: str) -> Dict[str, str]:
    """
    Extracts numbers, units, currency, and dates.
    Returns mapping: {normalized_key: raw_representation}
    """
    entities: Dict[str, str] = {}

    # Extract dates first
    for match in DATE_REGEX.finditer(text):
        raw = match.group(0).strip()
        norm = re.sub(r"\s+", " ", raw.lower().replace(",", ""))
        entities[f"date:{norm}"] = raw

    # Extract numbers with units / currency
    for match in NUM_UNIT_REGEX.finditer(text):
        raw = match.group(0).strip()
        if not raw:
            continue
        # Split number and suffix
        prefix = raw[0] if raw[0] in "$€£¥" else ""
        rest = raw[1:] if prefix else raw
        parts = rest.split()
        num_part = parts[0]
        unit_part = parts[1] if len(parts) > 1 else ""
        norm_num = normalize_number_string(num_part)
        norm_key = f"num:{prefix}{norm_num}_{unit_part.lower()}"
        entities[norm_key] = raw

    return entities


def audit_numeric_integrity(
    source_text: str, target_text: str, paragraph_index: int = None
) -> Tuple[NumericAuditResult, List[VerificationFinding]]:
    source_entities = extract_numeric_entities(source_text)
    target_entities = extract_numeric_entities(target_text)

    source_keys = set(source_entities.keys())
    target_keys = set(target_entities.keys())

    missing_keys = source_keys - target_keys
    added_keys = target_keys - source_keys

    missing_items = [source_entities[k] for k in missing_keys]
    added_items = [target_entities[k] for k in added_keys]

    findings: List[VerificationFinding] = []

    if missing_items:
        findings.append(
            VerificationFinding(
                category="numbers",
                severity="CRITICAL",
                code="NUMERIC_VALUE_DROPPED_OR_ALTERED",
                message=f"Original numerical value(s) missing or mutated in rewrite: {missing_items}",
                paragraph_index=paragraph_index,
                details={"missing": missing_items},
            )
        )

    if added_items:
        findings.append(
            VerificationFinding(
                category="numbers",
                severity="WARN",
                code="NUMERIC_VALUE_INTRODUCED",
                message=f"New numerical value(s) introduced in rewrite: {added_items}",
                paragraph_index=paragraph_index,
                details={"added": added_items},
            )
        )

    passed = len(missing_items) == 0

    result = NumericAuditResult(
        passed=passed,
        missing_numbers=missing_items,
        added_numbers=added_items,
        changed_numbers=[],
    )

    return result, findings
