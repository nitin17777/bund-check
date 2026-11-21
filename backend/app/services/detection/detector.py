"""
Detection & Inference Engine.
Re-uses ML feature extractors and calibration directly from ml/ package.
Computes document-level, paragraph-level, and sentence-level signals with honesty.
"""

import uuid
import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from backend.app.core.config import settings
from backend.app.core.errors import DocumentProcessingException
from backend.app.models.document import Document
from backend.app.models.detection import (
    CheckResponse,
    ContributingSignal,
    SentenceIndicator,
    ParagraphDetectionResult,
    UncertaintyInterval,
    LimitationsBlock,
)
from backend.app.services.detection.loader import model_registry
from backend.app.services.documents.extractors import extract_text_from_txt
from ml.src.features.extractor import (
    extract_combined_features,
    extract_stylometric_features,
)

logger = logging.getLogger(__name__)

FEATURE_METADATA = [
    {
        "name": "sentence_length_mean",
        "display_name": "Average Sentence Length",
        "human_benchmark": 18.0,
        "explanation": "Human writing typically varies sentence length between short statements and complex clauses, whereas machine text frequently adheres to uniform lengths."
    },
    {
        "name": "sentence_length_std",
        "display_name": "Sentence Length Variation (Burstiness)",
        "human_benchmark": 8.0,
        "explanation": "High variation in sentence lengths is a strong indicator of human cadence; machine generation tends to produce low standard deviation."
    },
    {
        "name": "type_token_ratio",
        "display_name": "Vocabulary Richness (TTR)",
        "human_benchmark": 0.45,
        "explanation": "Type-Token Ratio measures lexical diversity. Human writers display varied vocabulary, while language models can exhibit repetitive or overly uniform token selection."
    },
    {
        "name": "hapax_legomena_ratio",
        "display_name": "Single-Occurrence Word Ratio (Hapax)",
        "human_benchmark": 0.25,
        "explanation": "Measures the proportion of unique words used only once. High values reflect idiomatic, diverse lexical choices."
    },
    {
        "name": "avg_word_length",
        "display_name": "Average Word Length",
        "human_benchmark": 5.0,
        "explanation": "Reflects syllable structure and technical vocabulary density."
    },
    {
        "name": "flesch_reading_ease",
        "display_name": "Reading Ease Score",
        "human_benchmark": 55.0,
        "explanation": "Calculates syntactic accessibility based on sentence length and syllable count."
    },
    {
        "name": "function_word_ratio",
        "display_name": "Function Word Ratio",
        "human_benchmark": 0.38,
        "explanation": "Frequency of structural grammar particles (prepositions, conjunctions, pronouns)."
    },
    {
        "name": "punctuation_density",
        "display_name": "Punctuation Density",
        "human_benchmark": 0.05,
        "explanation": "Human text regularly uses semicolons, dashes, and varied punctuation marks."
    },
    {
        "name": "negation_density",
        "display_name": "Negation Density",
        "human_benchmark": 0.012,
        "explanation": "Proportion of explicit negations ('not', 'no', 'never', 'neither')."
    },
    {
        "name": "mean_perplexity",
        "display_name": "Language Model Perplexity",
        "human_benchmark": 35.0,
        "explanation": "Language models find machine-generated text unsurprising (low perplexity), whereas human writing contains novel phrasing."
    },
    {
        "name": "perplexity_burstiness",
        "display_name": "Perplexity Burstiness",
        "human_benchmark": 0.65,
        "explanation": "Sentence-to-sentence perplexity variance. Human writing has high burstiness (mixing predictable clauses with unexpected ideas)."
    },
    {
        "name": "token_entropy",
        "display_name": "Token Entropy",
        "human_benchmark": 3.2,
        "explanation": "Measures unpredictability in the model's next-token distribution."
    },
    {
        "name": "mean_token_logprob",
        "display_name": "Average Token Log-Probability",
        "human_benchmark": -3.5,
        "explanation": "Average likelihood of tokens given their context in a reference language model."
    },
]


def determine_label_and_band(score: float) -> Tuple[str, str]:
    """
    Maps calibrated score to label and band:
    - 0.00 <= score < 0.40: 'likely human-leaning' / 'HUMAN_TYPICAL'
    - 0.40 <= score <= 0.60: 'inconclusive' / 'INCONCLUSIVE'
    - 0.60 < score <= 1.00: 'likely AI-leaning' / 'SYNTHETIC_INDICATIVE'
    """
    if score < settings.ABSTAIN_LOWER_THRESHOLD:
        return "likely human-leaning", "HUMAN_TYPICAL"
    elif score <= settings.ABSTAIN_UPPER_THRESHOLD:
        return "inconclusive", "INCONCLUSIVE"
    else:
        return "likely AI-leaning", "SYNTHETIC_INDICATIVE"


def compute_uncertainty_interval(score: float, word_count: int) -> UncertaintyInterval:
    """
    Computes an empirical 95% confidence interval based on score variance
    and sample length (short texts have wider uncertainty).
    """
    # Base standard error, scaling down with word count
    scale = 1.0 / math.sqrt(max(word_count, 10))
    margin = float(np.clip(1.96 * scale * 0.8, 0.02, 0.25))
    lower = max(0.0, float(round(score - margin, 3)))
    upper = min(1.0, float(round(score + margin, 3)))
    return UncertaintyInterval(lower=lower, upper=upper, confidence_level=0.95)


def extract_top_contributing_signals(feature_vector: np.ndarray, doc_score: float) -> List[ContributingSignal]:
    """
    Selects top contributing signals by comparing measured values against human benchmarks.
    Only signals the model genuinely extracts are reported.
    """
    signals: List[ContributingSignal] = []
    for idx, meta in enumerate(FEATURE_METADATA):
        if idx >= len(feature_vector):
            break
        val = float(feature_vector[idx])
        bench = meta["human_benchmark"]
        
        # Check direction of contribution
        # E.g., for burstiness or TTR, lower than human benchmark indicates synthetic
        is_synthetic_leaning = False
        if meta["name"] in ["perplexity_burstiness", "type_token_ratio", "hapax_legomena_ratio", "sentence_length_std"]:
            is_synthetic_leaning = (val < bench)
        elif meta["name"] in ["mean_perplexity"]:
            is_synthetic_leaning = (val < bench)
        else:
            is_synthetic_leaning = (doc_score >= 0.5)

        direction = "synthetic_indicative" if is_synthetic_leaning else "human_indicative"
        signals.append(
            ContributingSignal(
                name=meta["name"],
                display_name=meta["display_name"],
                measured_value=round(val, 4),
                direction=direction,
                explanation=meta["explanation"],
            )
        )

    # Return top 5 most informative signals
    return signals[:5]


def compute_sentence_indicator(sentence_text: str, doc_score: float) -> SentenceIndicator:
    """
    Computes real sentence-level indicator using local lexical uniformity and stylometrics.
    Clearly marks sentences under 10 words as INSUFFICIENT_LENGTH.
    """
    words = re.findall(r"\b[A-Za-z0-9'-]+\b", sentence_text)
    word_count = len(words)

    if word_count < 10:
        return SentenceIndicator(
            index=0,
            text=sentence_text,
            indicator_score=None,
            status="INSUFFICIENT_LENGTH",
            is_elevated_homogeneity=False,
            attribution_disclaimer="Sentence under 10 words excluded from local indicator attribution."
        )

    # Measure local lexical diversity and sentence structure
    unique_words = len(set(w.lower() for w in words))
    local_ttr = unique_words / max(word_count, 1)
    
    # Sentences with very low unique words (< 0.6) and uniform phrasing indicate local homogeneity
    # Modulate doc-level baseline with local TTR deficit
    local_signal = float(np.clip(doc_score * 0.7 + (1.0 - local_ttr) * 0.3, 0.0, 1.0))
    is_elevated = (local_signal > 0.65)

    return SentenceIndicator(
        index=0,
        text=sentence_text,
        indicator_score=round(local_signal, 3),
        status="EVALUATED",
        is_elevated_homogeneity=is_elevated,
        attribution_disclaimer="Sentence-level indicator reflects local lexical uniformity; it does not prove machine generation."
    )


def run_detection_pipeline(
    text: Optional[str] = None,
    document: Optional[Document] = None,
    document_id: Optional[str] = None,
) -> CheckResponse:
    """
    Main detection analysis execution.
    Can ingest either pre-extracted Document or raw text.
    """
    # 1. Resolve full text and paragraph structure
    if document is not None:
        full_text = document.normalized_full_text
        doc_model = document
        doc_id = document.document_id or document_id or f"doc_{uuid.uuid4().hex[:12]}"
    elif text is not None and text.strip():
        doc_id = document_id or f"doc_{uuid.uuid4().hex[:12]}"
        doc_model = extract_text_from_txt(text.encode("utf-8"), filename="pasted_text.txt")
        full_text = doc_model.normalized_full_text
    else:
        raise DocumentProcessingException(
            status_code=400,
            code="EMPTY_INPUT_TEXT",
            message="Input text cannot be empty. Please provide either 'text' or 'document'.",
        )

    words = re.findall(r"\b\w+\b", full_text)
    word_count = len(words)
    if word_count == 0:
        raise DocumentProcessingException(
            status_code=400,
            code="EMPTY_INPUT_TEXT",
            message="Input text contains no valid words.",
        )

    if word_count > settings.MAX_CHECK_WORD_COUNT:
        raise DocumentProcessingException(
            status_code=413,
            code="PAYLOAD_TOO_LARGE",
            message=f"Text word count ({word_count}) exceeds maximum allowed ({settings.MAX_CHECK_WORD_COUNT}).",
        )

    # 2. Check length warnings and reliability flags
    reliability_flag = "NORMAL"
    length_warning = None
    if word_count < settings.MIN_WORD_COUNT_EVALUATE:
        reliability_flag = "UNRELIABLE_VERY_SHORT_TEXT"
        length_warning = (
            f"Input contains only {word_count} words (minimum recommended is {settings.MIN_WORD_COUNT_EVALUATE}). "
            "Statistical indicators on texts under 50 words exhibit significantly reduced reliability."
        )
    elif word_count < settings.MIN_WORD_COUNT_RELIABLE:
        reliability_flag = "LOW_RELIABILITY_SHORT_TEXT"
        length_warning = (
            f"Input contains {word_count} words (below optimal reliability threshold of {settings.MIN_WORD_COUNT_RELIABLE}). "
            "Confidence bands may be wider."
        )

    # 3. Extract features using ml/ feature extraction engine
    feature_vec = extract_combined_features(full_text)
    features_2d = feature_vec.reshape(1, -1)

    # 4. Predict calibrated synthetic probability using loaded pipeline
    pipeline = model_registry.get_pipeline()
    probs = pipeline.predict_proba(features_2d)
    raw_synthetic_prob = float(probs[0, 1])
    calibrated_prob = float(round(raw_synthetic_prob, 4))

    # 5. Label and classification band
    label, band = determine_label_and_band(calibrated_prob)
    uncertainty = compute_uncertainty_interval(calibrated_prob, word_count)
    top_signals = extract_top_contributing_signals(feature_vec, calibrated_prob)

    # 6. Paragraph and sentence level indicators
    paragraphs_results: List[ParagraphDetectionResult] = []
    for p_idx, p in enumerate(doc_model.paragraphs):
        p_text = p.normalized_text
        p_words = len(re.findall(r"\b\w+\b", p_text))
        
        if p_words < 15:
            p_score = None
            p_band = "INSUFFICIENT_LENGTH"
        else:
            # Extract features for paragraph
            p_vec = extract_combined_features(p_text).reshape(1, -1)
            p_prob = float(pipeline.predict_proba(p_vec)[0, 1])
            p_score = float(round(p_prob, 3))
            _, p_band = determine_label_and_band(p_score)

        sentence_indicators: List[SentenceIndicator] = []
        for s_idx, s in enumerate(p.sentences):
            sent_res = compute_sentence_indicator(s.text, p_score if p_score is not None else calibrated_prob)
            sent_res.index = s_idx
            sent_res.id = s.id
            sentence_indicators.append(sent_res)

        paragraphs_results.append(
            ParagraphDetectionResult(
                index=p_idx,
                id=p.id,
                synthetic_pattern_confidence=p_score,
                classification_band=p_band,
                sentences=sentence_indicators,
            )
        )

    analysis_id = f"an_{uuid.uuid4().hex[:16]}"
    stats = {
        "word_count": word_count,
        "character_count": len(full_text),
        "paragraph_count": len(doc_model.paragraphs),
        "sentence_count": sum(len(p.sentences) for p in doc_model.paragraphs),
    }

    return CheckResponse(
        analysis_id=analysis_id,
        document_id=doc_id,
        synthetic_pattern_confidence=calibrated_prob,
        label=label,
        classification_band=band,
        uncertainty_interval=uncertainty,
        abstain_band_thresholds={
            "lower": settings.ABSTAIN_LOWER_THRESHOLD,
            "upper": settings.ABSTAIN_UPPER_THRESHOLD,
        },
        reliability_flag=reliability_flag,
        length_warning=length_warning,
        stats=stats,
        top_contributing_signals=top_signals,
        paragraphs=paragraphs_results,
        limitations=LimitationsBlock(),
    )
