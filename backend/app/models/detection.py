"""
Detection Service Schemas conforming to API_SPEC.md and MODEL_CARD.md.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.document import Document


class ContributingSignal(BaseModel):
    name: str = Field(description="Signal identifier, e.g. 'type_token_ratio'")
    display_name: str = Field(description="Human readable signal title")
    measured_value: float = Field(description="Raw measured value for the document")
    direction: str = Field(description="'human_indicative' or 'synthetic_indicative'")
    explanation: str = Field(description="Plain language explanation of what this signal means")


class SentenceIndicator(BaseModel):
    index: int = Field(description="0-based index of sentence within paragraph")
    id: Optional[str] = Field(None, description="Stable identifier matching Document sentence, e.g. 'p0_s0'")
    text: str = Field(description="Sentence text")
    indicator_score: Optional[float] = Field(
        None,
        description="Local synthetic pattern score (0.0 to 1.0). Null if sentence is too short.",
    )
    status: str = Field(
        description="'EVALUATED', 'INSUFFICIENT_LENGTH', or 'BELOW_LOCAL_RELIABILITY_THRESHOLD'"
    )
    is_elevated_homogeneity: bool = Field(
        default=False,
        description="True if the local indicator exceeds high synthetic pattern threshold",
    )
    attribution_disclaimer: str = Field(
        default="Sentence-level indicator reflects local lexical uniformity; it does not prove machine generation."
    )


class ParagraphDetectionResult(BaseModel):
    index: int = Field(description="0-based index of paragraph")
    id: Optional[str] = Field(None, description="Stable identifier matching Document paragraph, e.g. 'p0'")
    synthetic_pattern_confidence: Optional[float] = Field(
        None,
        description="Paragraph level calibrated synthetic confidence. Null if paragraph is too short.",
    )
    classification_band: str = Field(
        description="'HUMAN_TYPICAL', 'INCONCLUSIVE', 'SYNTHETIC_INDICATIVE', or 'INSUFFICIENT_LENGTH'"
    )
    sentences: List[SentenceIndicator] = Field(default_factory=list)


class UncertaintyInterval(BaseModel):
    lower: float
    upper: float
    confidence_level: float = 0.95


class LimitationsBlock(BaseModel):
    disclaimer: str = Field(
        default="This analysis reflects statistical probability based on linguistic patterns and perplexity variance. It does not prove authorship. Human editorial review is recommended."
    )
    plain_language_limitations: List[str] = Field(
        default=[
            "Never Absolute Proof: A high score indicates statistical alignment with machine language models; it does not prove machine generation or disprove human authorship.",
            "Adversarial Paraphrasing & Human Editing: Heavy paraphrasing or hybrid human-machine editing substantially degrades detector reliability.",
            "Domain Shifts & Length Vulnerability: Dense technical, legal, or non-native English prose, as well as inputs under 150 words, naturally exhibit lower entropy and may yield less reliable scores."
        ]
    )
    model_version: str = "1.0.0"
    model_hash: str = "51a5e6e06236960b6c734b65f3d45a8c7ad37e90007b570dd1dd7ad0eabcadff"


class CheckRequest(BaseModel):
    text: Optional[str] = Field(None, description="Raw pasted text to check")
    document: Optional[Document] = Field(None, description="Pre-extracted Document structure from /api/v1/documents/extract")
    document_id: Optional[str] = Field(None, description="Optional client-provided document ID")


class CheckResponse(BaseModel):
    analysis_id: str
    document_id: Optional[str] = None
    synthetic_pattern_confidence: float = Field(
        description="Calibrated probability that text exhibits synthetic machine-generated patterns (0.0 to 1.0)"
    )
    label: str = Field(
        description="Decision wording: 'likely human-leaning', 'inconclusive', or 'likely AI-leaning'"
    )
    classification_band: str = Field(
        description="'HUMAN_TYPICAL', 'INCONCLUSIVE', or 'SYNTHETIC_INDICATIVE'"
    )
    uncertainty_interval: UncertaintyInterval
    abstain_band_thresholds: Dict[str, float] = Field(
        default={"lower": 0.40, "upper": 0.60}
    )
    reliability_flag: str = Field(
        description="'NORMAL', 'LOW_RELIABILITY_SHORT_TEXT', or 'UNRELIABLE_VERY_SHORT_TEXT'"
    )
    length_warning: Optional[str] = None
    stats: Dict[str, int]
    top_contributing_signals: List[ContributingSignal]
    paragraphs: List[ParagraphDetectionResult]
    limitations: LimitationsBlock


class ReportRequest(BaseModel):
    check_response: CheckResponse = Field(description="Completed CheckResponse data to compile into a report")
    format: str = Field(default="json", description="'json', 'html', or 'pdf'")
    title: Optional[str] = Field(default="AI Content Analysis Report", description="Report title")
