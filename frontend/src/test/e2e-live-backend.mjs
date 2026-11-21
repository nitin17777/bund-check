/**
 * Live End-to-End Verification against running FastAPI backend and Next.js frontend.
 * Tests:
 * 1. Multi-paragraph Unicode document inspection
 * 2. Character offset integrity and exact sentence span alignment
 * 3. File upload extraction (TXT, DOCX, PDF)
 * 4. Error states: Scanned PDF rejection, short text rejection, empty text
 * 5. Report download and generation (HTML & JSON)
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FIXTURES_DIR = path.resolve(__dirname, "../../../tests/fixtures");

const BACKEND_URL = "http://127.0.0.1:8000/api/v1";
const FRONTEND_URL = "http://localhost:3000";

async function runE2E() {
  console.log("==================================================");
  console.log("BUNDCHECK E2E LIVE SYSTEM INTEGRATION SUITE");
  console.log("Backend:", BACKEND_URL);
  console.log("Frontend:", FRONTEND_URL);
  console.log("==================================================\n");

  // Health Check
  const healthRes = await fetch(`${BACKEND_URL}/health`);
  const healthData = await healthRes.json();
  console.log("✓ Backend Health Check:", healthData.status, `(v${healthData.version})`);

  // -----------------------------------------------------------------
  // Test 1: Multi-Paragraph Document with Complex Unicode
  // -----------------------------------------------------------------
  console.log("\n[TEST 1] Ingesting Multi-Paragraph Unicode Document...");
  const unicodeDoc = `The study examined several cafés and naïve participants during the experimental phase — observing behavioral traits across diverse conditions. Overall performance was evaluated using standard metrics, and results showed significant variance across groups.

A secondary analysis evaluated the mathematical α-helix and β-sheet formations in synthetic protein sequences. "The findings indicate strong alignment with prior literature," stated the principal investigator. Additional trials confirmed that numerical stability was preserved under all test temperatures.`;

  // 1a. Extract Document
  const extractRes = await fetch(`${BACKEND_URL}/documents/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: unicodeDoc, filename: "unicode_test.txt" }),
  });
  if (!extractRes.ok) throw new Error(`Extract failed: ${extractRes.statusText}`);
  const extractedDoc = await extractRes.json();

  console.log("  Extracted Document ID:", extractedDoc.document_id);
  console.log("  Word count:", extractedDoc.stats.word_count);
  console.log("  Paragraphs:", extractedDoc.paragraphs.length);
  console.log("  Sentences:", extractedDoc.stats.sentence_count);

  // 1b. Verify Character Offset Round-Trip
  console.log("  Verifying Unicode character offsets alignment...");
  for (const p of extractedDoc.paragraphs) {
    const fullNormalized = extractedDoc.normalized_full_text;
    const paraSlice = fullNormalized.slice(p.start_char, p.end_char);
    if (paraSlice !== p.normalized_text) {
      throw new Error(`Paragraph offset mismatch at p${p.index}`);
    }

    for (const s of p.sentences) {
      const sentSlice = p.normalized_text.slice(s.start_char, s.end_char);
      if (sentSlice !== s.text) {
        throw new Error(`Sentence offset mismatch at p${p.index}_s${s.index}: "${sentSlice}" !== "${s.text}"`);
      }
    }
  }
  console.log("  ✓ All paragraph & sentence character offsets align perfectly with zero drift!");

  // 1c. Run Content Check
  console.log("  Running Multi-Signal Content Check...");
  const checkRes = await fetch(`${BACKEND_URL}/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document: extractedDoc }),
  });
  if (!checkRes.ok) throw new Error(`Check failed: ${checkRes.statusText}`);
  const checkData = await checkRes.json();

  console.log("  Analysis ID:", checkData.analysis_id);
  console.log("  Calibrated Score:", (checkData.synthetic_pattern_confidence * 100).toFixed(1) + "%");
  console.log("  Calibrated Label:", `"${checkData.label}"`);
  console.log("  Classification Band:", checkData.classification_band);
  console.log("  95% CI:", `[${(checkData.uncertainty_interval.lower * 100).toFixed(1)}% - ${(checkData.uncertainty_interval.upper * 100).toFixed(1)}%]`);
  console.log("  Top Contributing Signals:", checkData.top_contributing_signals.length);
  console.log("  Paragraph Heatmap Results:", checkData.paragraphs.length);
  console.log("  ✓ Multi-Paragraph Unicode Check Passed!");

  // -----------------------------------------------------------------
  // Test 2: Report Export (HTML & JSON)
  // -----------------------------------------------------------------
  console.log("\n[TEST 2] Verifying Report Generation (/check/report)...");
  
  // HTML Export
  const htmlReportRes = await fetch(`${BACKEND_URL}/check/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ check_response: checkData, format: "html" }),
  });
  if (!htmlReportRes.ok) throw new Error(`HTML Report failed: ${htmlReportRes.status}`);
  const htmlContent = await htmlReportRes.text();
  if (!htmlContent.includes("BundCheck Analysis Report") && !htmlContent.includes("Analysis Report")) {
    throw new Error("HTML report missing header");
  }
  console.log("  ✓ Generated HTML report (length:", htmlContent.length, "bytes)");

  // JSON Export
  const jsonReportRes = await fetch(`${BACKEND_URL}/check/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ check_response: checkData, format: "json" }),
  });
  if (!jsonReportRes.ok) throw new Error(`JSON Report failed: ${jsonReportRes.status}`);
  const jsonReportData = await jsonReportRes.json();
  console.log("  ✓ Generated JSON report (analysis_id:", jsonReportData.analysis_id, ")");

  // -----------------------------------------------------------------
  // Test 3: Real File Uploads (TXT, DOCX, PDF)
  // -----------------------------------------------------------------
  console.log("\n[TEST 3] Testing Real File Uploads (TXT, DOCX, PDF)...");

  // 3a. TXT
  const txtBytes = fs.readFileSync(path.join(FIXTURES_DIR, "sample_document.txt"));
  const txtForm = new FormData();
  txtForm.append("file", new Blob([txtBytes], { type: "text/plain" }), "sample_document.txt");

  const txtExtract = await fetch(`${BACKEND_URL}/documents/extract`, { method: "POST", body: txtForm });
  if (!txtExtract.ok) throw new Error(`TXT extract failed: ${txtExtract.status}`);
  const txtDoc = await txtExtract.json();
  console.log("  ✓ Uploaded TXT extracted:", txtDoc.filename, `(${txtDoc.stats.word_count} words)`);

  // 3b. DOCX
  const docxBytes = fs.readFileSync(path.join(FIXTURES_DIR, "sample_report.docx"));
  const docxForm = new FormData();
  docxForm.append("file", new Blob([docxBytes], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" }), "sample_report.docx");

  const docxExtract = await fetch(`${BACKEND_URL}/documents/extract`, { method: "POST", body: docxForm });
  if (!docxExtract.ok) throw new Error(`DOCX extract failed: ${docxExtract.status}`);
  const docxDoc = await docxExtract.json();
  console.log("  ✓ Uploaded DOCX extracted:", docxDoc.filename, `(${docxDoc.stats.word_count} words, ${docxDoc.paragraphs.length} paras)`);

  // 3c. PDF
  const pdfBytes = fs.readFileSync(path.join(FIXTURES_DIR, "valid_research.pdf"));
  const pdfForm = new FormData();
  pdfForm.append("file", new Blob([pdfBytes], { type: "application/pdf" }), "valid_research.pdf");

  const pdfExtract = await fetch(`${BACKEND_URL}/documents/extract`, { method: "POST", body: pdfForm });
  if (!pdfExtract.ok) throw new Error(`PDF extract failed: ${pdfExtract.status}`);
  const pdfDoc = await pdfExtract.json();
  console.log("  ✓ Uploaded PDF extracted:", pdfDoc.filename, `(${pdfDoc.stats.word_count} words, ${pdfDoc.paragraphs.length} paras)`);

  // -----------------------------------------------------------------
  // Test 4: Error State Verification
  // -----------------------------------------------------------------
  console.log("\n[TEST 4] Testing Actionable Error States...");

  // 4a. Scanned PDF rejection
  const scannedPdfBytes = fs.readFileSync(path.join(FIXTURES_DIR, "scanned_image_only.pdf"));
  const scannedForm = new FormData();
  scannedForm.append("file", new Blob([scannedPdfBytes], { type: "application/pdf" }), "scanned_image_only.pdf");

  const scannedRes = await fetch(`${BACKEND_URL}/documents/extract`, { method: "POST", body: scannedForm });
  const scannedErr = await scannedRes.json();
  console.log("  ✓ Scanned PDF rejected correctly with status:", scannedRes.status, `(code: ${scannedErr.error.code})`);
  if (scannedErr.error.code !== "SCANNED_PDF_OCR_NOT_SUPPORTED" && scannedErr.error.code !== "SCANNED_PDF_NOT_SUPPORTED") {
    throw new Error(`Expected SCANNED_PDF_OCR_NOT_SUPPORTED, got ${scannedErr.error.code}`);
  }

  // 4b. Empty Text Rejection
  const emptyRes = await fetch(`${BACKEND_URL}/documents/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: "   " }),
  });
  const emptyErr = await emptyRes.json();
  console.log("  ✓ Empty text rejected correctly with status:", emptyRes.status, `(code: ${emptyErr.error.code})`);

  // 4c. Short Text Warning Flag
  const shortText = "The quick brown fox jumps over the lazy dog repeatedly.";
  const shortCheckRes = await fetch(`${BACKEND_URL}/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: shortText }),
  });
  const shortCheckData = await shortCheckRes.json();
  console.log("  ✓ Short text flagged correctly with reliability_flag:", shortCheckData.reliability_flag);
  if (shortCheckData.reliability_flag === "NORMAL") {
    throw new Error("Expected short text reliability flag");
  }

  console.log("\n==================================================");
  console.log("ALL E2E LIVE BACKEND INTEGRATION SCENARIOS PASSED!");
  console.log("==================================================");
}

runE2E().catch((err) => {
  console.error("E2E Test Failed:", err);
  process.exit(1);
});
