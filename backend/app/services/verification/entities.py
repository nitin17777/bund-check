"""
Named Entity and Technical Term Verification Engine.

Uses spaCy en_core_web_sm for NER (PERSON, ORG, GPE, DATE, PRODUCT).
Falls back to a capitalized-word heuristic if the spaCy model is unavailable
(e.g. offline test environments).

Flags:
  - CRITICAL when a named entity from the source is absent in the target.
  - WARN when a new entity is introduced in the target.
  - WARN when a technical term (capitalized multi-word phrase not covered by NER)
    disappears from the target.
"""

import re
import logging
from typing import List, Tuple, Set, Optional, Dict

from backend.app.models.verification import VerificationFinding, EntityAuditResult

logger = logging.getLogger(__name__)

# Lazy-loaded spaCy NLP object — populated on first call.
_nlp = None

# Entity labels that matter for factual integrity.
RELEVANT_LABELS = {"PERSON", "ORG", "GPE", "DATE", "PRODUCT", "LAW", "FAC", "NORP", "EVENT"}

# Minimum length for a capitalized token to count as a potential technical term.
MIN_TECHNICAL_TERM_LEN = 3


def _load_nlp():
    """Lazy load en_core_web_sm; sets _nlp to None on failure (triggers fallback)."""
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy  # noqa: PLC0415
        _nlp = spacy.load("en_core_web_sm")
        logger.info("Loaded spaCy en_core_web_sm for entity verification.")
    except Exception as exc:
        logger.warning(
            "spaCy en_core_web_sm not available (%s). "
            "Falling back to capitalized-word heuristic for entity detection.",
            exc,
        )
        _nlp = None
    return _nlp


def _extract_entities_spacy(text: str) -> Set[str]:
    """Extract named entities using spaCy."""
    nlp = _load_nlp()
    if nlp is None:
        return set()
    doc = nlp(text)
    return {
        ent.text.strip()
        for ent in doc.ents
        if ent.label_ in RELEVANT_LABELS and len(ent.text.strip()) >= 2
    }


def _extract_entities_fallback(text: str) -> Set[str]:
    """
    Fallback: treat sequences of capitalized words (CamelCase / Title Case) as
    potential named entities / technical terms.  Ignores sentence-start capitals
    by requiring at least two consecutive capitalized tokens or one mid-sentence
    capitalized token.
    """
    # Tokenize into sentences first; skip the first token of each sentence.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    entities: Set[str] = set()
    for sent in sentences:
        tokens = sent.split()
        for i, token in enumerate(tokens):
            # Strip surrounding punctuation
            clean = re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", token)
            if (
                i > 0  # skip sentence-start
                and len(clean) >= MIN_TECHNICAL_TERM_LEN
                and clean[0].isupper()
                and not clean.isupper()  # ignore ALL-CAPS abbreviations (too noisy)
            ):
                entities.add(clean)
    return entities


def extract_entities(text: str) -> Tuple[Set[str], bool]:
    """
    Returns (entity_set, used_spacy).
    entity_set: set of entity/term strings found in text.
    used_spacy: True if spaCy was used, False if fallback was used.
    """
    nlp = _load_nlp()
    if nlp is not None:
        return _extract_entities_spacy(text), True
    return _extract_entities_fallback(text), False


def _extract_technical_terms(text: str) -> Set[str]:
    """
    Extract capitalized multi-word technical terms (e.g. 'Random Forest', 'DeBERTa-v3').
    These supplement NER output since NER may miss domain-specific jargon.
    """
    # Match: 2+ consecutive Title-Case or mixed-case tokens (allowing hyphens)
    pattern = re.compile(
        r"\b([A-Z][A-Za-z0-9\-]{1,}(?:\s+[A-Z][A-Za-z0-9\-]{1,})+)\b"
    )
    return {m.group(0).strip() for m in pattern.finditer(text)}


def audit_entity_integrity(
    source_text: str,
    target_text: str,
    paragraph_index: Optional[int] = None,
) -> Tuple[EntityAuditResult, List[VerificationFinding]]:
    """
    Compares named entities and technical terms between source and target.

    Returns:
        (EntityAuditResult, List[VerificationFinding])
    """
    source_entities, used_spacy = extract_entities(source_text)
    target_entities, _ = extract_entities(target_text)

    # Technical term overlay (applied regardless of spaCy availability)
    source_terms = _extract_technical_terms(source_text)
    target_terms = _extract_technical_terms(target_text)

    # Combine NER entities + technical terms
    all_source = source_entities | source_terms
    all_target = target_entities | target_terms

    missing = sorted(all_source - all_target)
    added = sorted(all_target - all_source)

    findings: List[VerificationFinding] = []

    if missing:
        findings.append(
            VerificationFinding(
                category="entities",
                severity="CRITICAL",
                code="ENTITY_DROPPED",
                message=(
                    f"Named entity or technical term(s) present in source but absent in rewrite: {missing}. "
                    f"Detection method: {'spaCy NER + multi-word terms' if used_spacy else 'capitalized-word heuristic + multi-word terms'}."
                ),
                paragraph_index=paragraph_index,
                details={
                    "missing_entities": missing,
                    "detection_method": "spacy" if used_spacy else "heuristic",
                },
            )
        )

    if added:
        findings.append(
            VerificationFinding(
                category="entities",
                severity="WARN",
                code="ENTITY_INTRODUCED",
                message=(
                    f"New named entity or technical term(s) introduced in rewrite: {added}. "
                    "Verify these are not fabricated."
                ),
                paragraph_index=paragraph_index,
                details={
                    "added_entities": added,
                    "detection_method": "spacy" if used_spacy else "heuristic",
                },
            )
        )

    passed = len(missing) == 0

    result = EntityAuditResult(
        passed=passed,
        missing_entities=missing,
        added_entities=added,
    )

    return result, findings
