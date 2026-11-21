"""
Helper script to generate real fixture documents in tests/fixtures/:
- multi-paragraph text with citations & math
- table docx
- unicode & ligatures text
- empty file
- wrong extension with valid content
- spoofed extension (.docx containing malicious/invalid text)
- oversized file
- encrypted PDF
- scanned-style PDF with no text (raster image only)
- zip-bomb-like DOCX
"""

import io
import os
import zipfile
import docx
import pymupdf as fitz

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
os.makedirs(FIXTURES_DIR, exist_ok=True)


def create_fixtures():
    # 1. Multi-paragraph TXT with citations & math
    txt_path = os.path.join(FIXTURES_DIR, "sample_document.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(
            "This is the first paragraph with citation [14] and formula ΔE = mc².\n\n"
            "The second paragraph analyzes 42.8% of specimens (Smith et al., 2020).\n"
            "Dr. Alan Grant noted: 'This demonstrates stability.'\n\n"
            "Third paragraph has bullet points:\n"
            "- Item 1: Accuracy is 98.5%\n"
            "- Item 2: Latency is < 50ms"
        )

    # 2. DOCX with headings, paragraphs, and tables
    docx_path = os.path.join(FIXTURES_DIR, "sample_report.docx")
    doc = docx.Document()
    doc.add_heading("Experimental Analysis Report", level=1)
    doc.add_paragraph("This is the introductory section explaining the benchmark methodology.")
    
    # Table
    tbl = doc.add_table(rows=3, cols=2)
    tbl.cell(0, 0).text = "Model"
    tbl.cell(0, 1).text = "Accuracy"
    tbl.cell(1, 0).text = "DistilRoBERTa"
    tbl.cell(1, 1).text = "94.2%"
    tbl.cell(2, 0).text = "Ensemble"
    tbl.cell(2, 1).text = "97.8%"
    
    doc.add_heading("Discussion and Conclusions", level=2)
    doc.add_paragraph("Overall results demonstrate robust calibration across domains.")
    doc.save(docx_path)

    # 3. Unicode and ligatures text
    unicode_path = os.path.join(FIXTURES_DIR, "unicode_ligatures.txt")
    with open(unicode_path, "w", encoding="utf-8") as f:
        f.write("The \ufb01rst \ufb02ight of the o\ufb03ce was e\ufb00ective in C\u0153ur.")

    # 4. Empty file
    empty_path = os.path.join(FIXTURES_DIR, "empty.txt")
    with open(empty_path, "wb") as f:
        f.write(b"")

    # 5. Wrong extension with valid content (Valid TXT named .pdf)
    wrong_ext_path = os.path.join(FIXTURES_DIR, "spoofed_text_as_pdf.pdf")
    with open(wrong_ext_path, "wb") as f:
        f.write(b"This is just plain text masquerading as a PDF file.")

    # 6. Spoofed extension (.docx containing random plain text, not a zip)
    spoofed_docx = os.path.join(FIXTURES_DIR, "spoofed_docx.docx")
    with open(spoofed_docx, "wb") as f:
        f.write(b"Plain text placed inside a .docx file.")

    # 7. Oversized file (> 10 MB)
    oversized_path = os.path.join(FIXTURES_DIR, "oversized.txt")
    with open(oversized_path, "wb") as f:
        # Write 10 MB + 1024 bytes
        f.write(b"A" * (10 * 1024 * 1024 + 1024))

    # 8. Encrypted PDF
    encrypted_pdf_path = os.path.join(FIXTURES_DIR, "encrypted.pdf")
    pdf_doc = fitz.open()
    page = pdf_doc.new_page()
    page.insert_text(fitz.Point(50, 72), "Confidential encrypted document.")
    # Encrypt PDF with password
    pdf_doc.save(
        encrypted_pdf_path,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="owner123",
        user_pw="secret123",
    )
    pdf_doc.close()

    # 9. Scanned-style PDF with no text (raster image only)
    scanned_pdf_path = os.path.join(FIXTURES_DIR, "scanned_image_only.pdf")
    scan_doc = fitz.open()
    scan_page = scan_doc.new_page(width=300, height=300)
    # Create a tiny 10x10 pixmap and insert as image
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), 0)
    scan_page.insert_image(fitz.Rect(50, 50, 250, 250), pixmap=pix)
    scan_doc.save(scanned_pdf_path)
    scan_doc.close()

    # 10. Zip-bomb-like DOCX (high compression ratio)
    bomb_docx_path = os.path.join(FIXTURES_DIR, "zip_bomb.docx")
    with zipfile.ZipFile(bomb_docx_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", "<w:document></w:document>")
        z.writestr("[Content_Types].xml", "<Types></Types>")
        # 30 MB of repetitive zeros which compresses down to ~30 KB (1000:1 ratio)
        z.writestr("word/huge_payload.dat", b"0" * (30 * 1024 * 1024))

    # 11. Normal valid PDF
    valid_pdf_path = os.path.join(FIXTURES_DIR, "valid_research.pdf")
    normal_pdf = fitz.open()
    n_page = normal_pdf.new_page()
    n_page.insert_text(fitz.Point(50, 72), "Standard research paper on probabilistic detection models.")
    n_page.insert_text(fitz.Point(50, 100), "Calibration shows reliable uncertainty bands [1].")
    normal_pdf.save(valid_pdf_path)
    normal_pdf.close()


if __name__ == "__main__":
    create_fixtures()
    print("All fixtures created successfully.")
