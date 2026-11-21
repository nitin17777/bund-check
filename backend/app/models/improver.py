"""
Pydantic Data Models for the Writing Improver Service.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

ImproverMode = Literal[
    "natural_conversational",
    "academic_clarity",
    "professional",
    "simple_readable",
    "concise",
    "formal",
]


class SentenceChange(BaseModel):
    sentence_index: int = Field(description="0-based sentence index within paragraph")
    original: str = Field(description="Original sentence text")
    revised: str = Field(description="Improved sentence text")
    accepted: bool = Field(default=True, description="Accept/reject status for interactive review")


class ParagraphImprovement(BaseModel):
    paragraph_index: int = Field(description="0-based paragraph index")
    original_text: str = Field(description="Original paragraph text")
    revised_text: str = Field(description="Improved paragraph text with restored protected spans")
    is_heading: bool = Field(default=False, description="Whether paragraph is a preserved heading")
    status: str = Field(default="SUCCESS", description="'SUCCESS', 'SKIPPED_HEADING', 'FAILED'")
    changes: List[SentenceChange] = Field(default_factory=list, description="Sentence-aligned edits")
    error_message: Optional[str] = None


class UsageAccounting(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class ImproveRequest(BaseModel):
    text: str = Field(description="Input text to improve")
    mode: ImproverMode = Field(
        default="academic_clarity",
        description="Rewrite style: natural_conversational, academic_clarity, professional, simple_readable, concise, formal"
    )
    provider: Optional[str] = Field(
        default=None,
        description="Override provider (e.g. 'groq', 'openrouter', 'openai', 'local_small'). Uses default if unset."
    )


class ImproveResponse(BaseModel):
    revision_id: str
    mode: ImproverMode
    provider_used: str
    model_used: str
    paragraphs: List[ParagraphImprovement]
    stats: Dict[str, int]
    usage: UsageAccounting
