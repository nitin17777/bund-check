"""
Paragraph Chunking Engine.
Splits document into paragraph-level chunks while preserving:
- Paragraph ordering
- Heading identification
- Short context windows for local coherence without token bloat
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.services.documents.extractors import extract_text_from_txt


class ParagraphChunk(BaseModel):
    chunk_index: int
    text: str
    is_heading: bool
    heading_level: Optional[int] = None
    prev_context: Optional[str] = None  # Brief preceding sentence for smooth transition


def chunk_document_for_improver(text: str) -> List[ParagraphChunk]:
    """
    Parses input text into ordered ParagraphChunks with heading detection and preceding context.
    """
    # Use our existing robust extractor
    doc = extract_text_from_txt(text.encode("utf-8"), filename="input.txt")
    chunks: List[ParagraphChunk] = []

    last_body_paragraph = ""
    for idx, p in enumerate(doc.paragraphs):
        p_text = p.normalized_text.strip()
        if not p_text:
            continue

        # Get the trailing sentence of previous body paragraph as context
        prev_ctx = None
        if last_body_paragraph and not p.is_heading:
            prev_sentences = re.split(r"[.!?]+", last_body_paragraph)
            valid_s = [s.strip() for s in prev_sentences if s.strip()]
            if valid_s:
                prev_ctx = valid_s[-1]

        # Heading detection heuristic for text chunks (e.g. Markdown headers # Title or p.is_heading)
        is_heading = p.is_heading
        heading_level = p.heading_level
        clean_text = p_text

        if not is_heading and p_text.startswith("#"):
            match = re.match(r"^(#{1,6})\s+(.*)$", p_text)
            if match:
                is_heading = True
                heading_level = len(match.group(1))
                clean_text = match.group(2).strip()

        chunks.append(
            ParagraphChunk(
                chunk_index=idx,
                text=clean_text,
                is_heading=is_heading,
                heading_level=heading_level,
                prev_context=prev_ctx,
            )
        )

        if not is_heading:
            last_body_paragraph = p_text

    return chunks
