"""
Export endpoints.

- POST /api/v1/export: produce DOCX, TXT, and PDF from the final accepted text.
"""

import io
import datetime
from typing import Optional

from fastapi import APIRouter, Body, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.app.deps import get_db
from backend.app.models.database import User, Document, Analysis, Revision
from sqlalchemy.orm import Session


router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    format: str = Field(..., description="'docx', 'txt', or 'pdf'")
    text: str = Field(..., description="The final accepted text to export")
    title: Optional[str] = Field(default="BundCheck Export", description="Document title")


class ExportResponse(BaseModel):
    success: bool
    format: str
    filename: str
    mime_type: str
    data: dict  # will contain base64 or indicate error


def export_to_docx(text: str, title: str = "Export") -> bytes:
    """Export text to DOCX format using python-docx.

    Preserves headings (lines starting with #), bold (**text**), italic *text*,
    and simple lists (- or * prefix). Documents what is lost.
    """
    from docx import Document as DocxDocument
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = DocxDocument()

    # Add title
    if title:
        title_heading = doc.add_heading(title, level=0)
        # Set title font
        for run in title_heading.runs:
            run.font.size = Pt(16)
            run.font.color.rgb = RGBColor(0, 0, 0)

    # Process text line by line to preserve structure
    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()

        # Heading detection: lines starting with #
        if stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")), 4)
            heading_text = stripped.lstrip("#").strip()
            heading = doc.add_heading(heading_text, level=level)
            for run in heading.runs:
                run.font.size = Pt(14 - level * 2)
                run.font.color.rgb = RGBColor(0, 0, 0)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            # List item
            doc.add_paragraph(stripped[2:], style="List Bullet")
        elif stripped == "":
            # Empty paragraph (line break)
            doc.add_paragraph("")
        elif stripped.startswith("**") and stripped.endswith("**"):
            # Bold text
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(stripped[2:-2])
            run.bold = True
        elif stripped.startswith("*") and stripped.endswith("*"):
            # Italic text
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(stripped[1:-1])
            run.italic = True
        else:
            # Plain paragraph
            doc.add_paragraph(stripped)

    # Save to bytes buffer
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def export_to_txt(text: str) -> bytes:
    """Export text to TXT format."""
    return text.encode("utf-8")


def export_to_pdf(text: str, title: str = "Export") -> bytes:
    """Export text to PDF format using reportlab.

    Creates a simple PDF with the title and text content.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.colors import HexColor

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=12,
        textColor=HexColor("#000000"),
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=6,
        textColor=HexColor("#000000"),
    )
    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6,
        textColor=HexColor("#000000"),
    )

    story = []

    # Add title
    if title:
        story.append(Paragraph(title, title_style))

    # Process text line by line
    lines = text.split("\n")
    for line in lines:
        stripped = line.strip()

        # Heading detection
        if stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")), 6)
            heading_text = stripped.lstrip("#").strip()
            story.append(Paragraph(heading_text, heading_style))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            # List item
            story.append(
                Paragraph(stripped[2:], ParagraphStyle("List", parent=normal_style, leftIndent=24)))
        elif stripped == "":
            story.append(Paragraph("<br/>", normal_style))
        elif stripped.startswith("**") and stripped.endswith("**"):
            # Bold text
            story.append(
                Paragraph(stripped[2:-2], ParagraphStyle("Bold", parent=normal_style, fontName="Helvetica-Bold")))
        elif "*" in stripped:
            # Italic text (heuristic)
            story.append(
                Paragraph(stripped, ParagraphStyle("Italic", parent=normal_style, fontName="Helvetica-Oblique")))
        else:
            # Plain paragraph
            story.append(Paragraph(stripped, normal_style))

    pdf.build(story)
    buffer.seek(0)
    return buffer.read()


@router.post("", status_code=status.HTTP_200_OK)
def export(
    request: Request,
    payload: ExportRequest,
    db: Session = Depends(get_db),
):
    """Export the final accepted text in DOCX, TXT, and PDF formats.

    Produces all three formats. The user can download whichever they need.
    For DOCX: attempts to preserve headings, paragraphs, basic formatting
    (bold/italic, lists) and documents known losses.
    For TXT: plain text round-trip.
    For PDF: formatted document.
    """
    results = {}

    # Always produce TXT
    txt_bytes = export_to_txt(payload.text)
    txt_filename = f"{payload.title or 'export'}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    results["txt"] = {
        "success": True,
        "filename": txt_filename,
        "mime_type": "text/plain",
        "data_base64": __import__("base64").b64encode(txt_bytes).decode("utf-8"),
    }

    # DOCX
    try:
        docx_bytes = export_to_docx(payload.text, payload.title or "Export")
        docx_filename = f"{payload.title or 'export'}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
        results["docx"] = {
            "success": True,
            "filename": docx_filename,
            "mime_type": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            "data_base64": __import__("base64").b64encode(docx_bytes).decode("utf-8"),
        }
    except Exception as e:
        results["docx"] = {
            "success": False,
            "filename": f"{payload.title or 'export'}_fallback.txt",
            "mime_type": "text/plain",
            "error": str(e),
            "note": "DOCX export unavailable. Known losses without python-docx: "
                    "headings not preserved as headings, bold/italic not preserved, "
                    "lists not preserved as bullet points. "
                    "Plain text content is still included.",
        }

    # PDF
    try:
        pdf_bytes = export_to_pdf(payload.text, payload.title or "Export")
        pdf_filename = f"{payload.title or 'export'}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        results["pdf"] = {
            "success": True,
            "filename": pdf_filename,
            "mime_type": "application/pdf",
            "data_base64": __import__("base64").b64encode(pdf_bytes).decode("utf-8"),
        }
    except Exception as e:
        results["pdf"] = {
            "success": False,
            "filename": f"{payload.title or 'export'}_fallback.txt",
            "mime_type": "text/plain",
            "error": str(e),
            "note": "PDF export unavailable. Fallback produces TXT format only.",
        }

    return {"results": results}