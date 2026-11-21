"""
Pydantic Data Models for Document, Paragraphs, Sentences, and Extraction Result.
Includes stable IDs and exact character offsets into the normalized text.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Sentence(BaseModel):
    id: str = Field(description="Stable unique identifier for sentence, e.g. p0_s0")
    index: int = Field(description="0-based sentence index within paragraph")
    text: str = Field(description="Sentence text")
    start_char: int = Field(description="Start character offset in normalized paragraph text")
    end_char: int = Field(description="End character offset in normalized paragraph text (exclusive)")
    char_count: int = Field(description="Character count of sentence")
    word_count: int = Field(description="Word count of sentence")


class Paragraph(BaseModel):
    id: str = Field(description="Stable unique identifier for paragraph, e.g. p0")
    index: int = Field(description="0-based paragraph index")
    raw_text: str = Field(description="Original unaltered extracted text for auditing")
    normalized_text: str = Field(description="Normalized text with ligatures, breaks, and Unicode cleaned")
    start_char: int = Field(description="Start character offset in full document normalized text")
    end_char: int = Field(description="End character offset in full document normalized text (exclusive)")
    is_table: bool = False
    is_heading: bool = False
    heading_level: Optional[int] = None
    char_count: int = Field(description="Character count of normalized paragraph")
    word_count: int = Field(description="Word count of normalized paragraph")
    sentences: List[Sentence] = Field(default_factory=list)


class DocumentStats(BaseModel):
    word_count: int
    character_count: int
    paragraph_count: int
    sentence_count: int
    page_count: Optional[int] = None


class UnsupportedElement(BaseModel):
    type: str  # e.g. "complex_table", "nested_table", "image", "scanned_page"
    location: str
    action_taken: str = "skipped"
    description: str


class Document(BaseModel):
    document_id: str
    filename: Optional[str] = None
    mime_type: str
    language: str = Field(default="en", description="Guessed language ISO code (e.g. 'en')")
    language_warning: Optional[str] = None
    stats: DocumentStats
    normalized_full_text: str = Field(description="Complete normalized text combining paragraphs")
    paragraphs: List[Paragraph]
    unsupported_elements: List[UnsupportedElement] = Field(default_factory=list)


class TextExtractRequest(BaseModel):
    text: str
    filename: Optional[str] = "pasted_text.txt"
