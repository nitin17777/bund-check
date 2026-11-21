"""
Document Parser & Table Ingestion Engine.

Implements robust extraction for PDF, DOCX, and TXT:
- Preserves raw extracted text separately from normalized text.
- Formats standard grid tables as Markdown pipe-tables.
- Identifies and skips unsupported table structures (nested, merged) and graphical elements.
- Records all skipped elements with precise locations in metadata.
- Outputs structured paragraph and sentence models.
"""

import io
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

import docx
import pymupdf as fitz

from backend.services.parser.normalizer import normalize_text, segment_sentences
from backend.services.parser.security import (
    validate_and_detect_document,
    MIME_PDF,
    MIME_DOCX,
    MIME_TXT,
    SecurityValidationError,
)


class SentenceModel(BaseModel):
    index: int
    text: str
    char_count: int


class ParagraphModel(BaseModel):
    index: int
    raw_text: str = Field(description="Unaltered raw extracted text for auditing")
    normalized_text: str = Field(description="Safely normalized text with ligatures/breaks resolved")
    is_table: bool = False
    char_count: int
    word_count: int
    sentences: List[SentenceModel] = Field(default_factory=list)


class UnsupportedElement(BaseModel):
    type: str  # e.g., "nested_table", "merged_cell_table", "image", "drawing"
    location: str
    action_taken: str = "skipped"
    description: str


class DocumentExtractionResult(BaseModel):
    filename: str
    mime_type: str
    total_words: int
    total_characters: int
    paragraph_count: int
    paragraphs: List[ParagraphModel]
    unsupported_elements: List[UnsupportedElement] = Field(default_factory=list)


def format_markdown_table(rows: List[List[str]]) -> Optional[str]:
    """
    Converts a 2D matrix of text cells into a standard Markdown pipe-table.
    Requires at least 1 row and 1 column.
    """
    if not rows or not rows[0]:
        return None

    # Clean cell values
    cleaned_rows = [[cell.replace("\n", " ").replace("|", "\\|").strip() for cell in row] for row in rows]
    num_cols = max(len(row) for row in cleaned_rows)

    # Pad rows that have fewer columns
    for row in cleaned_rows:
        while len(row) < num_cols:
            row.append("")

    # Construct table lines
    header = "| " + " | ".join(cleaned_rows[0]) + " |"
    separator = "| " + " | ".join(["---"] * num_cols) + " |"
    body_lines = ["| " + " | ".join(row) + " |" for row in cleaned_rows[1:]]

    return "\n".join([header, separator] + body_lines)


class DocumentParser:
    """
    Unified extraction service for document parsing.
    """

    def __init__(self, max_file_size_bytes: int = 10 * 1024 * 1024):
        self.max_file_size_bytes = max_file_size_bytes

    def parse_bytes(self, file_bytes: bytes, filename: str) -> DocumentExtractionResult:
        """
        Validates security and extracts document content into structured models.
        """
        mime_type = validate_and_detect_document(file_bytes, max_size_bytes=self.max_file_size_bytes)

        if mime_type == MIME_TXT:
            return self._parse_txt(file_bytes, filename)
        elif mime_type == MIME_DOCX:
            return self._parse_docx(file_bytes, filename)
        elif mime_type == MIME_PDF:
            return self._parse_pdf(file_bytes, filename)
        else:
            raise SecurityValidationError(f"Unsupported MIME type: {mime_type}")

    def _parse_txt(self, file_bytes: bytes, filename: str) -> DocumentExtractionResult:
        raw_text = file_bytes.decode("utf-8", errors="replace")
        paragraphs: List[ParagraphModel] = []
        unsupported_elements: List[UnsupportedElement] = []

        raw_blocks = [b.strip() for b in raw_text.split("\n\n") if b.strip()]
        total_words = 0
        total_chars = 0

        for idx, block in enumerate(raw_blocks):
            norm = normalize_text(block)
            if not norm:
                continue

            words = len(norm.split())
            chars = len(norm)
            total_words += words
            total_chars += chars

            sentences = [
                SentenceModel(index=s_idx, text=s, char_count=len(s))
                for s_idx, s in enumerate(segment_sentences(norm))
            ]

            paragraphs.append(
                ParagraphModel(
                    index=idx,
                    raw_text=block,
                    normalized_text=norm,
                    is_table=False,
                    char_count=chars,
                    word_count=words,
                    sentences=sentences,
                )
            )

        return DocumentExtractionResult(
            filename=filename,
            mime_type=MIME_TXT,
            total_words=total_words,
            total_characters=total_chars,
            paragraph_count=len(paragraphs),
            paragraphs=paragraphs,
            unsupported_elements=unsupported_elements,
        )

    def _parse_docx(self, file_bytes: bytes, filename: str) -> DocumentExtractionResult:
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs: List[ParagraphModel] = []
        unsupported_elements: List[UnsupportedElement] = []

        total_words = 0
        total_chars = 0
        para_idx = 0

        # Iterate over body elements (paragraphs and tables in order)
        for block in doc.element.body:
            tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag

            if tag == "p":
                # Standard paragraph
                text = block.text.strip() if block.text else ""
                if not text:
                    continue

                norm = normalize_text(text)
                if not norm:
                    continue

                words = len(norm.split())
                chars = len(norm)
                total_words += words
                total_chars += chars

                sentences = [
                    SentenceModel(index=s_idx, text=s, char_count=len(s))
                    for s_idx, s in enumerate(segment_sentences(norm))
                ]

                paragraphs.append(
                    ParagraphModel(
                        index=para_idx,
                        raw_text=text,
                        normalized_text=norm,
                        is_table=False,
                        char_count=chars,
                        word_count=words,
                        sentences=sentences,
                    )
                )
                para_idx += 1

            elif tag == "tbl":
                # Table element
                tbl = docx.table.Table(block, doc)
                matrix: List[List[str]] = []
                is_supported = True
                skip_reason = ""

                # Check for merged cells or unsupported nesting
                try:
                    # Detect merged cells by checking for duplicate cell proxies across a row or column
                    for row in tbl.rows:
                        seen_cells = set()
                        for cell in row.cells:
                            if cell._tc in seen_cells:
                                is_supported = False
                                skip_reason = "Merged table cells detected"
                                break
                            seen_cells.add(cell._tc)
                        if not is_supported:
                            break

                    if is_supported:
                        for row in tbl.rows:
                            row_cells = [cell.text.strip() for cell in row.cells]
                            matrix.append(row_cells)
                except Exception as e:
                    is_supported = False
                    skip_reason = f"Corrupted table grid: {str(e)}"

                if is_supported and matrix and len(matrix) >= 1:
                    # Check for irregular column lengths (indication of irregular merges)
                    num_cols = len(matrix[0])
                    for r in matrix:
                        if len(r) != num_cols:
                            is_supported = False
                            skip_reason = "Irregular or merged table cells"
                            break

                if is_supported and matrix:
                    md_table = format_markdown_table(matrix)
                    if md_table:
                        norm_table = normalize_text(md_table)
                        words = len(norm_table.split())
                        chars = len(norm_table)
                        total_words += words
                        total_chars += chars

                        paragraphs.append(
                            ParagraphModel(
                                index=para_idx,
                                raw_text=md_table,
                                normalized_text=norm_table,
                                is_table=True,
                                char_count=chars,
                                word_count=words,
                                sentences=[],
                            )
                        )
                        para_idx += 1
                else:
                    unsupported_elements.append(
                        UnsupportedElement(
                            type="complex_table",
                            location=f"body_block_{para_idx}",
                            action_taken="skipped",
                            description=skip_reason or "Unsupported nested or merged table layout",
                        )
                    )

        return DocumentExtractionResult(
            filename=filename,
            mime_type=MIME_DOCX,
            total_words=total_words,
            total_characters=total_chars,
            paragraph_count=len(paragraphs),
            paragraphs=paragraphs,
            unsupported_elements=unsupported_elements,
        )

    def _parse_pdf(self, file_bytes: bytes, filename: str) -> DocumentExtractionResult:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        paragraphs: List[ParagraphModel] = []
        unsupported_elements: List[UnsupportedElement] = []

        total_words = 0
        total_chars = 0
        para_idx = 0

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 1. Extract and process tables via PyMuPDF table finder
            page_tables = page.find_tables()
            table_bboxes = []

            for tbl_idx, tbl in enumerate(page_tables):
                try:
                    table_bboxes.append(tbl.bbox)
                    extracted_table = tbl.extract()
                    if extracted_table and len(extracted_table) >= 2:
                        md_table = format_markdown_table(extracted_table)
                        if md_table:
                            norm_table = normalize_text(md_table)
                            words = len(norm_table.split())
                            chars = len(norm_table)
                            total_words += words
                            total_chars += chars

                            paragraphs.append(
                                ParagraphModel(
                                    index=para_idx,
                                    raw_text=md_table,
                                    normalized_text=norm_table,
                                    is_table=True,
                                    char_count=chars,
                                    word_count=words,
                                    sentences=[],
                                )
                            )
                            para_idx += 1
                except Exception as e:
                    unsupported_elements.append(
                        UnsupportedElement(
                            type="pdf_table_error",
                            location=f"page_{page_num + 1}_table_{tbl_idx + 1}",
                            action_taken="skipped",
                            description=f"Could not convert PDF table: {str(e)}",
                        )
                    )

            # 2. Extract text blocks (excluding tables)
            blocks = page.get_text("blocks")
            for b in blocks:
                # b = (x0, y0, x1, y1, text, block_no, block_type)
                # block_type == 0 is text, 1 is image
                if b[6] == 1:
                    unsupported_elements.append(
                        UnsupportedElement(
                            type="image",
                            location=f"page_{page_num + 1}_block_{b[5]}",
                            action_taken="skipped",
                            description="Raster/vector image element skipped",
                        )
                    )
                    continue

                bbox = fitz.Rect(b[0], b[1], b[2], b[3])
                # Check if block overlaps with any extracted table
                overlaps_table = any(bbox.intersects(fitz.Rect(tb_bbox)) for tb_bbox in table_bboxes)
                if overlaps_table:
                    continue

                raw_block_text = b[4].strip()
                if not raw_block_text:
                    continue

                norm = normalize_text(raw_block_text)
                if not norm:
                    continue

                words = len(norm.split())
                chars = len(norm)
                total_words += words
                total_chars += chars

                sentences = [
                    SentenceModel(index=s_idx, text=s, char_count=len(s))
                    for s_idx, s in enumerate(segment_sentences(norm))
                ]

                paragraphs.append(
                    ParagraphModel(
                        index=para_idx,
                        raw_text=raw_block_text,
                        normalized_text=norm,
                        is_table=False,
                        char_count=chars,
                        word_count=words,
                        sentences=sentences,
                    )
                )
                para_idx += 1

        doc.close()

        return DocumentExtractionResult(
            filename=filename,
            mime_type=MIME_PDF,
            total_words=total_words,
            total_characters=total_chars,
            paragraph_count=len(paragraphs),
            paragraphs=paragraphs,
            unsupported_elements=unsupported_elements,
        )
