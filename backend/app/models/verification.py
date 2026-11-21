"""
Pydantic Models for Verification Engine.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

VerificationSeverity = Literal["INFO", "WARN", "CRITICAL"]
VerificationStatus = Literal["PASSED", "NEEDS_REVIEW", "FAILED"]


class VerificationFinding(BaseModel):
    category: str = Field(description="'numbers', 'citations', 'entities', 'structure', 'negations', 'semantics'")
    severity: VerificationSeverity
    code: str
    message: str
    paragraph_index: Optional[int] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ParagraphVerification(BaseModel):
    paragraph_index: int
    status: VerificationStatus
    needs_review: bool
    similarity_score: float = Field(description="Cosine similarity between source and revised paragraph")
    findings: List[VerificationFinding] = Field(default_factory=list)


class NumericAuditResult(BaseModel):
    passed: bool
    missing_numbers: List[str] = Field(default_factory=list)
    added_numbers: List[str] = Field(default_factory=list)
    changed_numbers: List[str] = Field(default_factory=list)


class CitationAuditResult(BaseModel):
    passed: bool
    missing_citations: List[str] = Field(default_factory=list)
    added_citations: List[str] = Field(default_factory=list)


class EntityAuditResult(BaseModel):
    passed: bool
    missing_entities: List[str] = Field(default_factory=list)
    added_entities: List[str] = Field(default_factory=list)


class StructureAuditResult(BaseModel):
    passed: bool
    source_count: int
    target_count: int
    status: str = Field(description="'ALIGNED', 'PARAGRAPH_COUNT_MISMATCH', 'PARAGRAPHS_MERGED_OR_SPLIT'")


class ChecksOverview(BaseModel):
    numeric_integrity: NumericAuditResult
    citation_integrity: CitationAuditResult
    entity_integrity: EntityAuditResult
    structure_integrity: StructureAuditResult
    negation_integrity: Dict[str, Any]
    semantic_integrity: Dict[str, Any]
    contradiction_check: Optional[Dict[str, Any]] = None


class VerificationReport(BaseModel):
    status: VerificationStatus
    overall_similarity_score: float
    similarity_note: str = Field(
        default="Embedding cosine similarity evaluates proximity in latent space; it does not guarantee logical equivalence."
    )
    needs_review: bool
    checks: ChecksOverview
    findings: List[VerificationFinding] = Field(default_factory=list)
    paragraph_verifications: List[ParagraphVerification] = Field(default_factory=list)


class VerifyRequest(BaseModel):
    source_text: str = Field(description="Original source text")
    target_text: str = Field(description="Rewritten or revised target text")
    enable_nli: bool = Field(default=False, description="Enable NLI contradiction checking (CPU bound)")
