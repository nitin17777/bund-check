"""
Document Extractors Engine.
Implements:
- PyMuPDF for PDF (scanned/image-only PDF detection, page extraction, tables).
- python-docx for DOCX (headings with levels, paragraphs, tables).
- Plain text with encoding detection (charset-normalizer fallback to utf-8).
- Detection of empty extracted text.
"""

import io
import uuid
from typing import List, Tuple, Optional
import charset_normalizer
import docx
import pymupdf as fitz

from backend.app.core.errors import DocumentProcessingException, ErrorDetail
from backend.app.models.document import (
    Document,
    Paragraph,
    DocumentStats,
    UnsupportedElement,
)
from backend.app.services.documents.segmentation import (
    normalize_paragraph_text,
    segment_sentences_with_offsets,
    guess_language,
)


def extract_text_from_txt(file_bytes: bytes, filename: Optional[str] = "input.txt") -> Document:
    # 1. Detect character encoding using charset-normalizer
    detection = charset_normalizer.from_bytes(file_bytes).best()
    if detection:
        encoding = detection.encoding
        try:
            raw_text = file_bytes.decode(encoding)
        except Exception:
            raw_text = file_bytes.decode("utf-8", errors="replace")
    else:
        raw_text = file_bytes.decode("utf-8", errors="replace")

    if not raw_text.strip():
        raise DocumentProcessingException(
            status_code=400,
            code="EMPTY_DOCUMENT_TEXT",
            message="No extractable text was found in the uploaded text document.",
            details=[ErrorDetail(field="text", issue="Document is empty or contains only whitespace.")],
        )

    # 2. Segment into paragraphs (normalize line breaks first to handle CRLF and LF)
    normalized_raw = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    raw_paragraphs = [p.strip() for p in normalized_raw.split("\n\n") if p.strip()]
    paragraphs: List[Paragraph] = []
    
    current_doc_offset = 0
    total_words = 0
    total_chars = 0
    total_sentences = 0
    full_text_parts: List[str] = []

    for idx, raw_p in enumerate(raw_paragraphs):
        norm_p = normalize_paragraph_text(raw_p)
        if not norm_p:
            continue

        p_id = f"p{idx}"
        p_len = len(norm_p)
        p_words = len(norm_p.split())
        sentences = segment_sentences_with_offsets(p_id, norm_p)

        p_start = current_doc_offset
        p_end = p_start + p_len
        current_doc_offset = p_end + 2  # account for \n\n between paragraphs

        total_words += p_words
        total_chars += p_len
        total_sentences += len(sentences)
        full_text_parts.append(norm_p)

        paragraphs.append(
            Paragraph(
                id=p_id,
                index=idx,
                raw_text=raw_p,
                normalized_text=norm_p,
                start_char=p_start,
                end_char=p_end,
                is_table=False,
                is_heading=False,
                heading_level=None,
                char_count=p_len,
                word_count=p_words,
                sentences=sentences,
            )
        )

    full_normalized_text = "\n\n".join(full_text_parts)
    lang, lang_warn = guess_language(full_normalized_text)

    return Document(
        document_id=f"doc_{uuid.uuid4().hex}",
        filename=filename,
        mime_type="text/plain",
        language=lang,
        language_warning=lang_warn,
        stats=DocumentStats(
            word_count=total_words,
            character_count=total_chars,
            paragraph_count=len(paragraphs),
            sentence_count=total_sentences,
            page_count=1,
        ),
        normalized_full_text=full_normalized_text,
        paragraphs=paragraphs,
        unsupported_elements=[],
    )


def extract_text_from_docx(file_bytes: bytes, filename: Optional[str] = "document.docx") -> Document:
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs: List[Paragraph] = []
    unsupported_elements: List[UnsupportedElement] = []

    current_doc_offset = 0
    total_words = 0
    total_chars = 0
    total_sentences = 0
    full_text_parts: List[str] = []
    para_idx = 0

    for block in doc.element.body:
        tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag

        if tag == "p":
            text = block.text.strip() if block.text else ""
            if not text:
                continue

            norm = normalize_paragraph_text(text)
            if not norm:
                continue

            # Check if paragraph is a heading
            is_heading = False
            heading_lvl = None
            p_obj = docx.text.paragraph.Paragraph(block, doc)
            if p_obj.style and p_obj.style.name:
                style_name = p_obj.style.name.lower()
                if "heading" in style_name:
                    is_heading = True
                    for num in range(1, 7):
                        if str(num) in style_name:
                            heading_lvl = num
                            break

            p_id = f"p{para_idx}"
            p_len = len(norm)
            p_words = len(norm.split())
            sentences = segment_sentences_with_offsets(p_id, norm)

            p_start = current_doc_offset
            p_end = p_start + p_len
            current_doc_offset = p_end + 2

            total_words += p_words
            total_chars += p_len
            total_sentences += len(sentences)
            full_text_parts.append(norm)

            paragraphs.append(
                Paragraph(
                    id=p_id,
                    index=para_idx,
                    raw_text=text,
                    normalized_text=norm,
                    start_char=p_start,
                    end_char=p_end,
                    is_table=False,
                    is_heading=is_heading,
                    heading_level=heading_lvl,
                    char_count=p_len,
                    word_count=p_words,
                    sentences=sentences,
                )
            )
            para_idx += 1

        elif tag == "tbl":
            tbl = docx.table.Table(block, doc)
            matrix: List[List[str]] = []
            is_supported = True
            skip_reason = ""

            try:
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
                        matrix.append([cell.text.strip() for cell in row.cells])
            except Exception as e:
                is_supported = False
                skip_reason = f"Corrupted table grid: {str(e)}"

            if is_supported and matrix and len(matrix) >= 1:
                # Convert to markdown pipe table
                cleaned_rows = [[c.replace("\n", " ").replace("|", "\\|").strip() for c in r] for r in matrix]
                num_cols = max(len(r) for r in cleaned_rows)
                for r in cleaned_rows:
                    while len(r) < num_cols:
                        r.append("")
                header = "| " + " | ".join(cleaned_rows[0]) + " |"
                sep = "| " + " | ".join(["---"] * num_cols) + " |"
                body = ["| " + " | ".join(r) + " |" for r in cleaned_rows[1:]]
                md_table = "\n".join([header, sep] + body)

                norm_table = normalize_paragraph_text(md_table)
                p_id = f"p{para_idx}"
                p_len = len(norm_table)
                p_words = len(norm_table.split())

                p_start = current_doc_offset
                p_end = p_start + p_len
                current_doc_offset = p_end + 2

                total_words += p_words
                total_chars += p_len
                full_text_parts.append(norm_table)

                paragraphs.append(
                    Paragraph(
                        id=p_id,
                        index=para_idx,
                        raw_text=md_table,
                        normalized_text=norm_table,
                        start_char=p_start,
                        end_char=p_end,
                        is_table=True,
                        is_heading=False,
                        heading_level=None,
                        char_count=p_len,
                        word_count=p_words,
                        sentences=[],
                    )
                )
                para_idx += 1
            else:
                unsupported_elements.append(
                    UnsupportedElement(
                        type="complex_table",
                        location=f"body_element_{para_idx}",
                        action_taken="skipped",
                        description=skip_reason or "Unsupported table layout",
                    )
                )

    if not paragraphs:
        raise DocumentProcessingException(
            status_code=400,
            code="EMPTY_DOCUMENT_TEXT",
            message="No extractable text was found in the DOCX document.",
            details=[ErrorDetail(field="file", issue="DOCX contains 0 text paragraphs or tables.")],
        )

    full_normalized_text = "\n\n".join(full_text_parts)
    lang, lang_warn = guess_language(full_normalized_text)

    return Document(
        document_id=f"doc_{uuid.uuid4().hex}",
        filename=filename,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        language=lang,
        language_warning=lang_warn,
        stats=DocumentStats(
            word_count=total_words,
            character_count=total_chars,
            paragraph_count=len(paragraphs),
            sentence_count=total_sentences,
            page_count=None,
        ),
        normalized_full_text=full_normalized_text,
        paragraphs=paragraphs,
        unsupported_elements=unsupported_elements,
    )


def extract_text_from_pdf(file_bytes: bytes, filename: Optional[str] = "document.pdf") -> Document:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = len(doc)
    paragraphs: List[Paragraph] = []
    unsupported_elements: List[UnsupportedElement] = []

    current_doc_offset = 0
    total_words = 0
    total_chars = 0
    total_sentences = 0
    full_text_parts: List[str] = []
    para_idx = 0

    total_extracted_text_len = 0
    has_images = False

    for page_num in range(page_count):
        page = doc[page_num]
        
        # Check for image elements
        image_list = page.get_images()
        if image_list:
            has_images = True

        # 1. Extract tables
        page_tables = page.find_tables()
        table_bboxes = []
        for tbl_idx, tbl in enumerate(page_tables):
            try:
                table_bboxes.append(tbl.bbox)
                extracted_tbl = tbl.extract()
                if extracted_tbl and len(extracted_tbl) >= 2:
                    cleaned_rows = [[c.replace("\n", " ").replace("|", "\\|").strip() if c else "" for c in r] for r in extracted_tbl]
                    num_cols = max(len(r) for r in cleaned_rows)
                    for r in cleaned_rows:
                        while len(r) < num_cols:
                            r.append("")
                    header = "| " + " | ".join(cleaned_rows[0]) + " |"
                    sep = "| " + " | ".join(["---"] * num_cols) + " |"
                    body = ["| " + " | ".join(r) + " |" for r in cleaned_rows[1:]]
                    md_table = "\n".join([header, sep] + body)

                    norm_table = normalize_paragraph_text(md_table)
                    p_id = f"p{para_idx}"
                    p_len = len(norm_table)
                    p_words = len(norm_table.split())

                    p_start = current_doc_offset
                    p_end = p_start + p_len
                    current_doc_offset = p_end + 2

                    total_words += p_words
                    total_chars += p_len
                    total_extracted_text_len += p_len
                    full_text_parts.append(norm_table)

                    paragraphs.append(
                        Paragraph(
                            id=p_id,
                            index=para_idx,
                            raw_text=md_table,
                            normalized_text=norm_table,
                            start_char=p_start,
                            end_char=p_end,
                            is_table=True,
                            is_heading=False,
                            heading_level=None,
                            char_count=p_len,
                            word_count=p_words,
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

        # 2. Extract text blocks
        blocks = page.get_text("blocks")
        for b in blocks:
            # b: (x0, y0, x1, y1, text, block_no, block_type)
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
            if any(bbox.intersects(fitz.Rect(tb_bbox)) for tb_bbox in table_bboxes):
                continue

            raw_block = b[4].strip()
            if not raw_block:
                continue

            norm_block = normalize_paragraph_text(raw_block)
            if not norm_block:
                continue

            p_id = f"p{para_idx}"
            p_len = len(norm_block)
            p_words = len(norm_block.split())
            sentences = segment_sentences_with_offsets(p_id, norm_block)

            p_start = current_doc_offset
            p_end = p_start + p_len
            current_doc_offset = p_end + 2

            total_words += p_words
            total_chars += p_len
            total_sentences += len(sentences)
            total_extracted_text_len += p_len
            full_text_parts.append(norm_block)

            paragraphs.append(
                Paragraph(
                    id=p_id,
                    index=para_idx,
                    raw_text=raw_block,
                    normalized_text=norm_block,
                    start_char=p_start,
                    end_char=p_end,
                    is_table=False,
                    is_heading=False,
                    heading_level=None,
                    char_count=p_len,
                    word_count=p_words,
                    sentences=sentences,
                )
            )
            para_idx += 1

    doc.close()

    # Detect scanned / image-only PDFs
    if total_extracted_text_len < 10 and has_images:
        raise DocumentProcessingException(
            status_code=422,
            code="SCANNED_PDF_OCR_NOT_SUPPORTED",
            message="This PDF appears to be a scanned document or image-only file. OCR is not supported yet.",
            details=[ErrorDetail(field="file", issue="No embedded text detected in image-bearing PDF.")],
        )

    if not paragraphs:
        raise DocumentProcessingException(
            status_code=400,
            code="EMPTY_DOCUMENT_TEXT",
            message="No extractable text was found in the PDF document.",
            details=[ErrorDetail(field="file", issue="PDF contains 0 text blocks.")],
        )

    full_normalized_text = "\n\n".join(full_text_parts)
    lang, lang_warn = guess_language(full_normalized_text)

    return Document(
        document_id=f"doc_{uuid.uuid4().hex}",
        filename=filename,
        mime_type="application/pdf",
        language=lang,
        language_warning=lang_warn,
        stats=DocumentStats(
            word_count=total_words,
            character_count=total_chars,
            paragraph_count=len(paragraphs),
            sentence_count=total_sentences,
            page_count=page_count,
        ),
        normalized_full_text=full_normalized_text,
        paragraphs=paragraphs,
        unsupported_elements=unsupported_elements,
    )
