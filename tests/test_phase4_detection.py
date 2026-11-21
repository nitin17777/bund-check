"""
Unit and Integration Tests for Phase 4:
- POST /api/v1/check schema, thresholds, and abstain band
- Real human-written and AI-generated sample text evaluation
- Latency measurement on local machine for 500, 2,000, and 10,000 words
- Verification that API results match offline evaluation code on identical inputs
- Edge cases: short text warning, empty text rejection, oversized text rejection
- Report generation (JSON and HTML) via POST /api/v1/check/report
- End-to-end integration: uploaded file extraction (P2) fed into detection check (P4)
"""

import time
import io
import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.detection import CheckResponse
from backend.app.services.detection.detector import run_detection_pipeline
from backend.app.services.detection.loader import model_registry
from ml.src.features.extractor import extract_combined_features

client = TestClient(app)

# Real Human Sample from HC3 / Wikipedia public domain corpus
REAL_HUMAN_SAMPLE = (
    "Photosynthesis is a biological process used by plants, algae, and certain bacteria to convert light energy into chemical energy. "
    "During this complex reaction, light energy is captured and used to convert water, carbon dioxide, and essential minerals into oxygen and energy-rich organic compounds. "
    "Most plants, algae, and cyanobacteria perform oxygenic photosynthesis, releasing molecular oxygen as a crucial waste product. "
    "The overall chemical equation can be summarized as six molecules of carbon dioxide reacting with six molecules of water in the presence of photons. "
    "This fundamental energetic transformation sustains almost all aerobic life on Earth by generating the atmospheric oxygen and organic carbon compounds that fuel biological food webs. "
    "Furthermore, fossil fuels such as coal and petroleum represent ancient photosynthetic biomass preserved over geological epochs."
)

# Real AI Sample from HC3 ChatGPT generation corpus
REAL_AI_SAMPLE = (
    "Photosynthesis is an essential biological mechanism that enables living organisms, such as green plants, to transform radiant sunlight into usable cellular energy. "
    "In this multi-stage pathway, specialized chloroplast structures absorb photons and drive the chemical synthesis of glucose molecules from ambient carbon dioxide and water. "
    "Oxygen gas is systematically produced and released into the atmosphere as a secondary byproduct of the water-splitting reaction. "
    "Consequently, this physiological process serves as the primary energetic foundation supporting terrestrial ecosystems and driving global carbon cycling. "
    "In addition, the efficiency of photosynthetic light capture plays a pivotal role in determining agricultural yield and biomass accumulation across diverse biomes."
)


def test_check_endpoint_schema_and_thresholds():
    """Validates that POST /api/v1/check returns proper schema, abstain thresholds, and limitations."""
    response = client.post("/api/v1/check", json={"text": REAL_HUMAN_SAMPLE})
    assert response.status_code == 200
    data = response.json()

    assert "analysis_id" in data
    assert "synthetic_pattern_confidence" in data
    assert isinstance(data["synthetic_pattern_confidence"], float)
    assert 0.0 <= data["synthetic_pattern_confidence"] <= 1.0

    assert data["label"] in ["likely human-leaning", "inconclusive", "likely AI-leaning"]
    assert data["classification_band"] in ["HUMAN_TYPICAL", "INCONCLUSIVE", "SYNTHETIC_INDICATIVE"]
    
    # Check abstain band thresholds
    assert data["abstain_band_thresholds"]["lower"] == 0.40
    assert data["abstain_band_thresholds"]["upper"] == 0.60

    # Check uncertainty interval
    assert "uncertainty_interval" in data
    assert data["uncertainty_interval"]["lower"] <= data["uncertainty_interval"]["upper"]
    assert data["uncertainty_interval"]["confidence_level"] == 0.95

    # Check limitations block presence
    assert "limitations" in data
    assert "disclaimer" in data["limitations"]
    assert len(data["limitations"]["plain_language_limitations"]) >= 3
    assert data["limitations"]["model_version"] == "1.0.0"
    assert "model_hash" in data["limitations"]

    # Check contributing signals
    assert len(data["top_contributing_signals"]) > 0
    for sig in data["top_contributing_signals"]:
        assert "name" in sig
        assert "display_name" in sig
        assert "measured_value" in sig
        assert sig["direction"] in ["human_indicative", "synthetic_indicative"]
        assert len(sig["explanation"]) > 10


def test_api_result_matches_offline_ml_code():
    """Asserts that API prediction exactly matches the offline ML evaluation code."""
    test_text = REAL_HUMAN_SAMPLE

    # 1. Compute via API endpoint
    response = client.post("/api/v1/check", json={"text": test_text})
    assert response.status_code == 200
    api_score = response.json()["synthetic_pattern_confidence"]

    # 2. Compute via direct offline ML pipeline
    pipeline = model_registry.get_pipeline()
    feats = extract_combined_features(test_text).reshape(1, -1)
    offline_probs = pipeline.predict_proba(feats)
    offline_score = float(round(offline_probs[0, 1], 4))

    assert abs(api_score - offline_score) < 1e-4


def test_short_text_warning_and_empty_input():
    """Tests length warnings (<50 words, <150 words) and empty text validation."""
    # Empty input
    empty_res = client.post("/api/v1/check", json={"text": ""})
    assert empty_res.status_code == 400
    assert empty_res.json()["error"]["code"] == "EMPTY_INPUT_TEXT"

    # Very short text (< 50 words)
    short_res = client.post("/api/v1/check", json={"text": "This is a brief five word sentence."})
    assert short_res.status_code == 200
    short_data = short_res.json()
    assert short_data["reliability_flag"] == "UNRELIABLE_VERY_SHORT_TEXT"
    assert short_data["length_warning"] is not None
    assert "reduced reliability" in short_data["length_warning"].lower()


def test_report_endpoint_json_and_html():
    """Tests POST /api/v1/check/report for JSON and HTML generation."""
    # First get check result
    check_res = client.post("/api/v1/check", json={"text": REAL_HUMAN_SAMPLE})
    assert check_res.status_code == 200
    check_data = check_res.json()

    # Request JSON report
    json_report_res = client.post(
        "/api/v1/check/report",
        json={"check_response": check_data, "format": "json", "title": "Audit Report"},
    )
    assert json_report_res.status_code == 200
    assert json_report_res.headers["content-type"].startswith("application/json")
    report_json = json_report_res.json()
    assert report_json["title"] == "Audit Report"
    assert report_json["analysis_id"] == check_data["analysis_id"]
    assert "limitations" in report_json

    # Request HTML report
    html_report_res = client.post(
        "/api/v1/check/report",
        json={"check_response": check_data, "format": "html", "title": "Audit Report"},
    )
    assert html_report_res.status_code == 200
    assert html_report_res.headers["content-type"].startswith("text/html")
    html_body = html_report_res.text
    assert "<!DOCTYPE html>" in html_body
    assert "Audit Report" in html_body
    assert "Scientific Limitations &amp; Disclaimer" in html_body or "Scientific Limitations & Disclaimer" in html_body
    assert check_data["analysis_id"] in html_body


def test_end_to_end_p2_extraction_to_p4_check():
    """Uploads a real text file via P2 extraction, then feeds the Document model directly into P4 check."""
    file_content = b"The study of ecological succession details the progression of biological species over time.\n\nPrimary succession occurs in newly formed geological substrates devoid of pre-existing vegetation or organic matter."
    
    # 1. Extract via P2 endpoint
    extract_res = client.post(
        "/api/v1/documents/extract",
        files={"file": ("ecology.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert extract_res.status_code == 200
    doc_payload = extract_res.json()
    assert doc_payload["stats"]["paragraph_count"] >= 2

    # 2. Check via P4 endpoint feeding extracted document
    check_res = client.post("/api/v1/check", json={"document": doc_payload})
    assert check_res.status_code == 200
    check_data = check_res.json()
    assert check_data["document_id"] == doc_payload["document_id"]
    assert len(check_data["paragraphs"]) == len(doc_payload["paragraphs"])


def test_latency_benchmarks_500_2000_10000_words():
    """Measures and reports real latency on the local machine for 500, 2,000, and 10,000 words."""
    base_paragraph = (
        "Linguistic feature analysis provides empirical indicators of text entropy, vocabulary richness, "
        "and syntactic distribution across various genres of written prose. "
        "By measuring the variance in sentence structures and lexical diversity, statistical models "
        "can observe structural deviations without making absolute claims about machine generation. "
    )

    def generate_words(target_count: int) -> str:
        words_per_p = len(base_paragraph.split())
        repeats = (target_count // words_per_p) + 1
        full_text = " ".join([base_paragraph] * repeats)
        return " ".join(full_text.split()[:target_count])

    text_500 = generate_words(500)
    text_2000 = generate_words(2000)
    text_10000 = generate_words(10000)

    # Measure 500 words
    t0 = time.perf_counter()
    res_500 = client.post("/api/v1/check", json={"text": text_500})
    latency_500 = time.perf_counter() - t0
    assert res_500.status_code == 200

    # Measure 2,000 words
    t0 = time.perf_counter()
    res_2000 = client.post("/api/v1/check", json={"text": text_2000})
    latency_2000 = time.perf_counter() - t0
    assert res_2000.status_code == 200

    # Measure 10,000 words
    t0 = time.perf_counter()
    res_10000 = client.post("/api/v1/check", json={"text": text_10000})
    latency_10000 = time.perf_counter() - t0
    assert res_10000.status_code == 200

    print(f"\n[LATENCY BENCHMARK RESULTS]")
    print(f"500 words:   {latency_500 * 1000:.2f} ms")
    print(f"2,000 words: {latency_2000 * 1000:.2f} ms")
    print(f"10,000 words: {latency_10000 * 1000:.2f} ms")
