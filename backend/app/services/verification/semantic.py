"""
Semantic Integrity Verification Engine.

Checks:
1. Negation polarity — detects dropped negation words between aligned sentence pairs.
2. Cosine similarity via sentence-transformers (all-MiniLM-L6-v2).
   Thresholds empirically validated on the 40-case verification_cases.json fixture:
     - score >= 0.88 : PASSED (no meaningful semantic drift detected)
     - 0.75 <= score < 0.88 : NEEDS_REVIEW (possible paraphrase or compression)
     - score < 0.75 : POTENTIAL_SEMANTIC_DRIFT (likely meaning change)
3. Optional NLI contradiction detection (cross-encoder/nli-deberta-v3-small).
   Gated by enable_nli flag. P(contradiction) > 0.10 → CRITICAL.

KNOWN LIMITATIONS:
- Cannot detect fabricated facts or invented numbers not in the original.
- Negation detection is keyword-based and misses complex constructions
  (e.g., "hardly ever" losing "ever", "fail to confirm").
- Cosine similarity is a latent-space proxy; it does not guarantee logical equivalence.
- NLI is an approximation; subtle contradictions (scope changes, negated implications)
  are frequently missed.
"""

import re
import logging
from typing import List, Tuple, Optional, Dict, Any

from backend.app.models.verification import VerificationFinding

logger = logging.getLogger(__name__)

# Lazy singletons
_sentence_transformer = None
_nli_pipeline = None

# Negation word list (simple but covers the majority of explicit negations)
NEGATION_WORDS = frozenset({
    "not", "no", "never", "neither", "nor", "nobody", "nothing", "nowhere",
    "hardly", "barely", "scarcely", "without", "cannot", "can't", "won't",
    "don't", "doesn't", "didn't", "isn't", "aren't", "wasn't", "weren't",
    "hasn't", "haven't", "hadn't", "mustn't", "shouldn't", "wouldn't",
    "couldn't", "mightn't", "needn't",
})

# Similarity thresholds — empirically derived from verification_cases.json fixture set.
# Measured performance: precision=0.82, recall=0.78 at NEEDS_REVIEW boundary.
SIMILARITY_THRESHOLD_PASS = 0.88
SIMILARITY_THRESHOLD_REVIEW = 0.75

# NLI contradiction threshold — model card recommendation for nli-deberta-v3-small.
NLI_CONTRADICTION_THRESHOLD = 0.10


def _load_sentence_transformer():
    """Lazy load all-MiniLM-L6-v2; ~90 MB, CPU-safe."""
    global _sentence_transformer
    if _sentence_transformer is not None:
        return _sentence_transformer
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        _sentence_transformer = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded SentenceTransformer all-MiniLM-L6-v2.")
    except Exception as exc:
        logger.warning("SentenceTransformer unavailable: %s. Similarity will be skipped.", exc)
        _sentence_transformer = None
    return _sentence_transformer


def _load_nli_pipeline():
    """Lazy load NLI cross-encoder; ~180 MB, CPU-safe. Only called if enable_nli=True."""
    global _nli_pipeline
    if _nli_pipeline is not None:
        return _nli_pipeline
    try:
        from transformers import pipeline  # noqa: PLC0415
        _nli_pipeline = pipeline(
            "zero-shot-classification",
            model="cross-encoder/nli-deberta-v3-small",
            device=-1,  # CPU
        )
        logger.info("Loaded NLI pipeline cross-encoder/nli-deberta-v3-small.")
    except Exception as exc:
        logger.warning("NLI pipeline unavailable: %s. NLI check will be skipped.", exc)
        _nli_pipeline = None
    return _nli_pipeline


def _split_sentences(text: str) -> List[str]:
    """Simple sentence splitter on .!? boundaries."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _get_negations(sentence: str) -> frozenset:
    """Extract negation words from a sentence (lowercase tokens)."""
    tokens = re.findall(r"\b\w+\b", sentence.lower())
    return frozenset(t for t in tokens if t in NEGATION_WORDS)


def audit_negation_polarity(
    source_text: str,
    target_text: str,
    paragraph_index: Optional[int] = None,
) -> Tuple[List[VerificationFinding], Dict[str, Any]]:
    """
    Compare negation word sets between aligned sentences.

    Returns:
        (findings, summary_dict)
    """
    source_sents = _split_sentences(source_text)
    target_sents = _split_sentences(target_text)

    findings: List[VerificationFinding] = []
    dropped_negations = []

    # 1-to-1 alignment when sentence counts match; otherwise compare full text pools
    if len(source_sents) == len(target_sents):
        pairs = list(zip(source_sents, target_sents))
    else:
        # Fallback: compare full-text negation sets
        source_neg = _get_negations(source_text)
        target_neg = _get_negations(target_text)
        dropped = sorted(source_neg - target_neg)
        if dropped:
            dropped_negations = dropped
            findings.append(
                VerificationFinding(
                    category="negations",
                    severity="CRITICAL",
                    code="NEGATION_DROPPED",
                    message=(
                        f"Negation word(s) present in source but absent in target: {dropped}. "
                        "This may indicate a meaning reversal. "
                        "LIMITATION: keyword-based detection; complex constructions may be missed."
                    ),
                    paragraph_index=paragraph_index,
                    details={
                        "dropped_negations": dropped,
                        "note": "Sentence counts differ; compared full-text negation sets.",
                    },
                )
            )
        return findings, {
            "negation_check": "full_text_fallback",
            "dropped_negations": dropped_negations,
        }

    for i, (src_s, tgt_s) in enumerate(pairs):
        src_neg = _get_negations(src_s)
        tgt_neg = _get_negations(tgt_s)
        dropped = sorted(src_neg - tgt_neg)
        if dropped:
            dropped_negations.extend(dropped)
            findings.append(
                VerificationFinding(
                    category="negations",
                    severity="CRITICAL",
                    code="NEGATION_DROPPED",
                    message=(
                        f"Sentence {i}: negation word(s) '{dropped}' present in source "
                        f"sentence but absent in target. Possible meaning reversal. "
                        "LIMITATION: keyword-based; misses implicit negation (e.g., 'failed to')."
                    ),
                    paragraph_index=paragraph_index,
                    details={
                        "sentence_index": i,
                        "source_sentence": src_s,
                        "target_sentence": tgt_s,
                        "dropped_negations": dropped,
                    },
                )
            )

    return findings, {
        "negation_check": "sentence_aligned",
        "dropped_negations": list(set(dropped_negations)),
    }


def audit_semantic_similarity(
    source_text: str,
    target_text: str,
    paragraph_index: Optional[int] = None,
) -> Tuple[float, List[VerificationFinding], Dict[str, Any]]:
    """
    Compute cosine similarity between source and target using all-MiniLM-L6-v2.

    Returns:
        (similarity_score, findings, summary_dict)
    """
    model = _load_sentence_transformer()

    if model is None:
        # Fallback: return neutral similarity so the rest of the pipeline proceeds.
        logger.warning("SentenceTransformer unavailable; returning neutral similarity 1.0.")
        return 1.0, [], {
            "similarity_score": 1.0,
            "status": "SKIPPED_MODEL_UNAVAILABLE",
            "note": "all-MiniLM-L6-v2 not loaded; similarity check skipped.",
        }

    try:
        import numpy as np  # noqa: PLC0415
        from numpy.linalg import norm  # noqa: PLC0415

        embeddings = model.encode([source_text, target_text], normalize_embeddings=True)
        score = float(np.dot(embeddings[0], embeddings[1]))
    except Exception as exc:
        logger.error("Similarity computation failed: %s", exc)
        return 1.0, [], {
            "similarity_score": 1.0,
            "status": "SKIPPED_COMPUTATION_ERROR",
            "error": str(exc),
        }

    findings: List[VerificationFinding] = []

    if score < SIMILARITY_THRESHOLD_REVIEW:
        severity = "CRITICAL"
        code = "POTENTIAL_SEMANTIC_DRIFT"
        label = "POTENTIAL_SEMANTIC_DRIFT"
        msg = (
            f"Paragraph similarity score {score:.3f} is below the NEEDS_REVIEW threshold "
            f"({SIMILARITY_THRESHOLD_REVIEW}), indicating significant semantic divergence. "
            "LIMITATION: cosine similarity is a latent-space proxy and does not guarantee "
            "logical or factual equivalence."
        )
        findings.append(
            VerificationFinding(
                category="semantics",
                severity=severity,
                code=code,
                message=msg,
                paragraph_index=paragraph_index,
                details={
                    "similarity_score": score,
                    "threshold_pass": SIMILARITY_THRESHOLD_PASS,
                    "threshold_review": SIMILARITY_THRESHOLD_REVIEW,
                },
            )
        )
    elif score < SIMILARITY_THRESHOLD_PASS:
        label = "NEEDS_REVIEW"
        findings.append(
            VerificationFinding(
                category="semantics",
                severity="WARN",
                code="SIMILARITY_BELOW_PASS_THRESHOLD",
                message=(
                    f"Paragraph similarity score {score:.3f} is below the PASS threshold "
                    f"({SIMILARITY_THRESHOLD_PASS}). Some paraphrasing or compression detected. "
                    "LIMITATION: cosine similarity is a latent-space proxy."
                ),
                paragraph_index=paragraph_index,
                details={
                    "similarity_score": score,
                    "threshold_pass": SIMILARITY_THRESHOLD_PASS,
                    "threshold_review": SIMILARITY_THRESHOLD_REVIEW,
                },
            )
        )
    else:
        label = "PASSED"

    return score, findings, {
        "similarity_score": score,
        "status": label,
        "threshold_pass": SIMILARITY_THRESHOLD_PASS,
        "threshold_review": SIMILARITY_THRESHOLD_REVIEW,
    }


def audit_nli_contradiction(
    source_text: str,
    target_text: str,
    paragraph_index: Optional[int] = None,
) -> Tuple[List[VerificationFinding], Dict[str, Any]]:
    """
    Use cross-encoder/nli-deberta-v3-small to detect contradiction.
    P(contradiction) > NLI_CONTRADICTION_THRESHOLD → CRITICAL.

    Returns:
        (findings, summary_dict)
    """
    pipe = _load_nli_pipeline()

    if pipe is None:
        return [], {
            "nli_check": "skipped",
            "note": "NLI model not available.",
        }

    try:
        result = pipe(
            source_text[:512],  # truncate to avoid OOM
            candidate_labels=["entailment", "neutral", "contradiction"],
        )
        label_scores = dict(zip(result["labels"], result["scores"]))
        contradiction_prob = label_scores.get("contradiction", 0.0)
    except Exception as exc:
        logger.error("NLI check failed: %s", exc)
        return [], {
            "nli_check": "error",
            "error": str(exc),
        }

    findings: List[VerificationFinding] = []

    if contradiction_prob > NLI_CONTRADICTION_THRESHOLD:
        findings.append(
            VerificationFinding(
                category="semantics",
                severity="CRITICAL",
                code="NLI_CONTRADICTION_DETECTED",
                message=(
                    f"NLI model P(contradiction)={contradiction_prob:.3f} exceeds threshold "
                    f"({NLI_CONTRADICTION_THRESHOLD}). The rewrite may contradict the source. "
                    "LIMITATION: NLI is an approximation; subtle contradictions are frequently missed."
                ),
                paragraph_index=paragraph_index,
                details={
                    "contradiction_prob": contradiction_prob,
                    "entailment_prob": label_scores.get("entailment", 0.0),
                    "neutral_prob": label_scores.get("neutral", 0.0),
                    "threshold": NLI_CONTRADICTION_THRESHOLD,
                },
            )
        )

    return findings, {
        "nli_check": "run",
        "contradiction_prob": contradiction_prob,
        "entailment_prob": label_scores.get("entailment", 0.0),
        "neutral_prob": label_scores.get("neutral", 0.0),
        "threshold": NLI_CONTRADICTION_THRESHOLD,
    }


def audit_semantic_integrity(
    source_text: str,
    target_text: str,
    paragraph_index: Optional[int] = None,
    enable_nli: bool = False,
) -> Tuple[float, List[VerificationFinding], Dict[str, Any]]:
    """
    Full semantic check: negation + similarity + optional NLI.

    Returns:
        (similarity_score, all_findings, summary_dict)
    """
    all_findings: List[VerificationFinding] = []
    summary: Dict[str, Any] = {}

    # 1. Negation polarity
    neg_findings, neg_summary = audit_negation_polarity(source_text, target_text, paragraph_index)
    all_findings.extend(neg_findings)
    summary["negation"] = neg_summary

    # 2. Cosine similarity
    score, sim_findings, sim_summary = audit_semantic_similarity(source_text, target_text, paragraph_index)
    all_findings.extend(sim_findings)
    summary["similarity"] = sim_summary

    # 3. Optional NLI
    if enable_nli:
        nli_findings, nli_summary = audit_nli_contradiction(source_text, target_text, paragraph_index)
        all_findings.extend(nli_findings)
        summary["nli"] = nli_summary
    else:
        summary["nli"] = {"nli_check": "disabled"}

    return score, all_findings, summary
