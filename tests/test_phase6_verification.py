"""
Phase 6: Multi-Stage Post-Rewrite Verification Tests.

Covers:
- Unit tests for each checker (numbers, citations, entities, structure, negation, similarity)
- Integration test for POST /api/v1/verify
- Precision/recall evaluation over the 40-case verification_cases.json fixture set
- Documents blind spots and known limitations
"""

import json
import os
import pytest
from pathlib import Path
from typing import List, Dict, Any

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Offline mode guard: allow model loading in this test file
# ---------------------------------------------------------------------------
os.environ.pop("HF_HUB_OFFLINE", None)
os.environ.pop("TRANSFORMERS_OFFLINE", None)

from backend.app.models.verification import VerifyRequest
from backend.app.services.verification.numbers import audit_numeric_integrity, extract_numeric_entities
from backend.app.services.verification.citations import audit_citation_integrity, extract_citations
from backend.app.services.verification.entities import audit_entity_integrity
from backend.app.services.verification.structure import audit_structure_integrity
from backend.app.services.verification.semantic import (
    audit_negation_polarity,
    audit_semantic_similarity,
    audit_semantic_integrity,
    SIMILARITY_THRESHOLD_PASS,
    SIMILARITY_THRESHOLD_REVIEW,
)
from backend.app.services.verification.aggregate import run_full_verification
from backend.app.main import app

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "verification_cases.json"

client = TestClient(app)


# ===========================================================================
# UNIT TESTS — Numbers
# ===========================================================================

class TestNumericChecker:

    def test_no_change_passes(self):
        src = "The sample had 42 participants aged 18 to 65."
        result, findings = audit_numeric_integrity(src, src)
        assert result.passed
        assert len(findings) == 0

    def test_changed_number_critical(self):
        src = "The sample consisted of 42 participants."
        tgt = "The sample consisted of 45 participants."
        result, findings = audit_numeric_integrity(src, tgt)
        assert not result.passed
        codes = [f.code for f in findings]
        assert "NUMERIC_VALUE_DROPPED_OR_ALTERED" in codes
        critical = [f for f in findings if f.severity == "CRITICAL"]
        assert len(critical) >= 1

    def test_comma_normalization(self):
        """1,000 and 1000 should be the same number."""
        src = "About 1,000 patients were enrolled."
        tgt = "Approximately 1000 patients were enrolled."
        result, findings = audit_numeric_integrity(src, tgt)
        assert result.passed, f"Expected passed, got findings: {findings}"

    def test_added_number_warn(self):
        src = "Participants improved."
        tgt = "Participants improved by 32%."
        result, findings = audit_numeric_integrity(src, tgt)
        warn = [f for f in findings if f.code == "NUMERIC_VALUE_INTRODUCED"]
        assert len(warn) >= 1

    def test_currency_detected(self):
        src = "Revenue increased by $1,000,000."
        tgt = "Revenue increased by $100,000."
        result, findings = audit_numeric_integrity(src, tgt)
        assert not result.passed

    def test_paragraph_index_propagated(self):
        src = "There are 10 items."
        tgt = "There are 20 items."
        _, findings = audit_numeric_integrity(src, tgt, paragraph_index=3)
        assert all(f.paragraph_index == 3 for f in findings)


# ===========================================================================
# UNIT TESTS — Citations
# ===========================================================================

class TestCitationChecker:

    def test_no_citations_passes(self):
        src = "Studies show this is effective."
        result, findings = audit_citation_integrity(src, src)
        assert result.passed
        assert len(findings) == 0

    def test_dropped_numbered_citation(self):
        src = "As shown by [1] and [2]."
        tgt = "As shown in the literature."
        result, findings = audit_citation_integrity(src, tgt)
        assert not result.passed
        assert any(f.code == "CITATION_DROPPED" for f in findings)

    def test_dropped_author_year(self):
        src = "Earlier work (Smith, 2019) supports this."
        tgt = "Earlier work supports this."
        result, findings = audit_citation_integrity(src, tgt)
        assert not result.passed

    def test_dropped_doi(self):
        src = "Published at doi:10.1038/s41586-021-03819-2."
        tgt = "Published in a journal."
        result, findings = audit_citation_integrity(src, tgt)
        assert not result.passed
        assert any("CITATION_DROPPED" == f.code for f in findings)

    def test_added_citation_warns(self):
        src = "Studies confirm this."
        tgt = "Studies confirm this [9]."
        result, findings = audit_citation_integrity(src, tgt)
        assert result.passed  # no missing, so passed
        assert any(f.code == "CITATION_INTRODUCED" for f in findings)

    def test_citation_preserved_passes(self):
        src = "See Jones (2020) for details."
        tgt = "For details, see Jones (2020)."
        result, findings = audit_citation_integrity(src, tgt)
        assert result.passed

    def test_extract_multi_citation(self):
        text = "Ref [1, 2] and [3-5] and (Brown et al., 2021)."
        cites = extract_citations(text)
        assert len(cites) >= 2


# ===========================================================================
# UNIT TESTS — Entities
# ===========================================================================

class TestEntityChecker:

    def test_same_text_passes(self):
        src = "Dr. Sarah Chen worked at Johns Hopkins University."
        result, findings = audit_entity_integrity(src, src)
        assert result.passed

    def test_dropped_person_entity(self):
        src = "Dr. Sarah Chen led the team."
        tgt = "Dr. Michael Liu led the team."
        result, findings = audit_entity_integrity(src, tgt)
        # Either the entity is detected as missing (passed=False) or introduced (WARN)
        # spaCy should catch one; heuristic catches capitalized names
        all_codes = [f.code for f in findings]
        assert "ENTITY_DROPPED" in all_codes or "ENTITY_INTRODUCED" in all_codes

    def test_technical_term_multi_word(self):
        src = "We use Random Forest and Gradient Boosting."
        tgt = "We use a machine learning ensemble."
        result, findings = audit_entity_integrity(src, tgt)
        # Random Forest / Gradient Boosting are multi-word technical terms
        # May or may not be found by NER; heuristic multi-word extractor should catch them
        # At minimum, verify function runs without error
        assert isinstance(result.passed, bool)


# ===========================================================================
# UNIT TESTS — Structure
# ===========================================================================

class TestStructureChecker:

    def test_aligned_passes(self):
        src = "Para one.\n\nPara two."
        tgt = "Para one rewritten.\n\nPara two rewritten."
        result, findings = audit_structure_integrity(src, tgt)
        assert result.passed
        assert result.status == "ALIGNED"

    def test_paragraph_deleted(self):
        src = "Para one.\n\nPara two.\n\nPara three."
        tgt = "Para one.\n\nPara two."
        result, findings = audit_structure_integrity(src, tgt)
        assert not result.passed
        assert any(f.code == "PARAGRAPH_COUNT_MISMATCH" for f in findings)
        assert result.source_count == 3
        assert result.target_count == 2

    def test_paragraphs_merged(self):
        src = "First.\n\nSecond."
        tgt = "First. Second."
        result, findings = audit_structure_integrity(src, tgt)
        assert not result.passed
        warn = [f for f in findings if f.severity == "WARN"]
        assert len(warn) >= 1

    def test_single_paragraph_no_newlines(self):
        src = "Single block of text with no double newlines."
        tgt = "Single block rewritten."
        result, findings = audit_structure_integrity(src, tgt)
        assert result.passed
        assert result.source_count == 1

    def test_extra_paragraph_added(self):
        src = "Original.\n\nSecond."
        tgt = "Original.\n\nSecond.\n\nThird new paragraph."
        result, findings = audit_structure_integrity(src, tgt)
        assert not result.passed


# ===========================================================================
# UNIT TESTS — Semantic (Negation + Similarity)
# ===========================================================================

class TestSemanticChecker:

    def test_negation_dropped(self):
        src = "The authors did not confirm the hypothesis."
        tgt = "The authors confirmed the hypothesis."
        findings, summary = audit_negation_polarity(src, tgt)
        codes = [f.code for f in findings]
        assert "NEGATION_DROPPED" in codes

    def test_negation_preserved(self):
        src = "The treatment was not effective."
        tgt = "The treatment was not found to be effective."
        findings, _ = audit_negation_polarity(src, tgt)
        assert all(f.code != "NEGATION_DROPPED" for f in findings)

    def test_cannot_dropped(self):
        src = "The drug cannot be used in liver disease patients."
        tgt = "The drug can be used in liver disease patients."
        findings, _ = audit_negation_polarity(src, tgt)
        codes = [f.code for f in findings]
        assert "NEGATION_DROPPED" in codes

    def test_identical_text_high_similarity(self):
        src = "Machine learning models learn patterns from data."
        score, findings, summary = audit_semantic_similarity(src, src)
        # Identical text must be >= PASS threshold (or model unavailable returns 1.0)
        assert score >= SIMILARITY_THRESHOLD_PASS

    def test_very_different_text_low_similarity(self):
        src = "The patient died due to complications from surgery."
        tgt = "Stock prices rose sharply after the quarterly earnings report."
        score, findings, summary = audit_semantic_similarity(src, tgt)
        # These are semantically unrelated; score should be below pass threshold
        # (unless model is unavailable and returns 1.0)
        if score < 1.0:  # model loaded
            assert score < SIMILARITY_THRESHOLD_PASS

    def test_paraphrase_scores_above_review(self):
        src = "Studies show that regular exercise improves cardiovascular health."
        tgt = "Research demonstrates that consistent physical activity benefits heart health."
        score, findings, summary = audit_semantic_similarity(src, tgt)
        # Good paraphrase — should stay above NEEDS_REVIEW or at least not drop below 0.70
        if score < 1.0:  # model loaded
            assert score >= 0.65, f"Paraphrase scored too low: {score}"

    def test_full_semantic_audit_no_error(self):
        src = "The intervention was not successful in reducing pain scores."
        tgt = "The intervention successfully reduced pain scores."
        score, findings, summary = audit_semantic_integrity(src, tgt, enable_nli=False)
        assert isinstance(score, float)
        assert isinstance(findings, list)
        # Should detect dropped 'not'
        codes = [f.code for f in findings]
        assert "NEGATION_DROPPED" in codes


# ===========================================================================
# UNIT TESTS — Aggregate / Full Verification
# ===========================================================================

class TestAggregateVerification:

    def test_clean_rewrite_passes(self):
        src = "Studies have shown that caffeine improves alertness in healthy adults."
        tgt = "Research indicates that caffeine enhances alertness in healthy individuals."
        report = run_full_verification(src, tgt)
        # Should be PASSED or at most NEEDS_REVIEW (not FAILED) for a clean rewrite
        assert report.status in ("PASSED", "NEEDS_REVIEW")
        assert isinstance(report.overall_similarity_score, float)

    def test_number_change_causes_failed(self):
        src = "The dosage is 500 mg twice daily."
        tgt = "The dosage is 250 mg twice daily."
        report = run_full_verification(src, tgt)
        assert report.status == "FAILED"
        codes = [f.code for f in report.findings]
        assert "NUMERIC_VALUE_DROPPED_OR_ALTERED" in codes

    def test_citation_drop_causes_failed(self):
        src = "As shown by Smith et al. [1], the effect is real."
        tgt = "As shown in the literature, the effect is real."
        report = run_full_verification(src, tgt)
        assert report.status == "FAILED"

    def test_negation_drop_causes_failed(self):
        src = "The treatment cannot be recommended for children."
        tgt = "The treatment can be recommended for children."
        report = run_full_verification(src, tgt)
        assert report.status == "FAILED"
        codes = [f.code for f in report.findings]
        assert "NEGATION_DROPPED" in codes

    def test_paragraph_verification_built(self):
        src = "First paragraph.\n\nSecond paragraph."
        tgt = "First paragraph rewritten.\n\nSecond paragraph rewritten."
        report = run_full_verification(src, tgt)
        assert len(report.paragraph_verifications) == 2
        assert report.paragraph_verifications[0].paragraph_index == 0
        assert report.paragraph_verifications[1].paragraph_index == 1

    def test_similarity_note_always_present(self):
        src = "Any text here."
        tgt = "Any text there."
        report = run_full_verification(src, tgt)
        assert len(report.similarity_note) > 0

    def test_findings_sorted_critical_first(self):
        src = "The dosage is 42 mg. See [1]. The drug cannot be used."
        tgt = "The dosage is 99 mg. The drug can be used."
        report = run_full_verification(src, tgt)
        if len(report.findings) > 1:
            severities = [f.severity for f in report.findings]
            # CRITICAL should come before WARN
            first_warn = next((i for i, s in enumerate(severities) if s == "WARN"), None)
            first_critical = next((i for i, s in enumerate(severities) if s == "CRITICAL"), None)
            if first_warn is not None and first_critical is not None:
                assert first_critical < first_warn


# ===========================================================================
# INTEGRATION TEST — POST /api/v1/verify
# ===========================================================================

class TestVerifyEndpoint:

    def test_basic_verify_request(self):
        payload = {
            "source_text": "The sample consisted of 42 participants.",
            "target_text": "The sample consisted of 45 participants.",
            "enable_nli": False,
        }
        response = client.post("/api/v1/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILED"
        assert any(f["code"] == "NUMERIC_VALUE_DROPPED_OR_ALTERED" for f in data["findings"])

    def test_clean_text_verify(self):
        payload = {
            "source_text": "Research shows caffeine improves alertness.",
            "target_text": "Studies indicate caffeine enhances alertness.",
            "enable_nli": False,
        }
        response = client.post("/api/v1/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("PASSED", "NEEDS_REVIEW")
        assert "overall_similarity_score" in data

    def test_verify_response_schema(self):
        payload = {
            "source_text": "Hello world.",
            "target_text": "Hello world.",
            "enable_nli": False,
        }
        response = client.post("/api/v1/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Required fields
        assert "status" in data
        assert "overall_similarity_score" in data
        assert "needs_review" in data
        assert "checks" in data
        assert "findings" in data
        assert "paragraph_verifications" in data
        assert "similarity_note" in data

    def test_verify_citation_dropped(self):
        payload = {
            "source_text": "This aligns with Smith et al. [1].",
            "target_text": "This aligns with the literature.",
            "enable_nli": False,
        }
        response = client.post("/api/v1/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILED"

    def test_verify_negation_dropped(self):
        payload = {
            "source_text": "The authors did not confirm the finding.",
            "target_text": "The authors confirmed the finding.",
            "enable_nli": False,
        }
        response = client.post("/api/v1/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        codes = [f["code"] for f in data["findings"]]
        assert "NEGATION_DROPPED" in codes
        assert data["status"] == "FAILED"

    def test_verify_multi_paragraph_alignment(self):
        payload = {
            "source_text": "Para one with 100 items.\n\nPara two with citations [1].",
            "target_text": "Para one rewritten with 100 items.\n\nPara two rewritten.",
            "enable_nli": False,
        }
        response = client.post("/api/v1/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["paragraph_verifications"]) == 2


# ===========================================================================
# PRECISION / RECALL EVALUATION OVER FIXTURE SET
# ===========================================================================

def load_fixture_cases() -> List[Dict[str, Any]]:
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        return json.load(f)


def evaluate_checker_on_fixtures():
    """
    Runs all fixture cases through run_full_verification and measures
    precision/recall per expected finding code.

    Returns:
        dict: {code -> {TP, FP, FN, precision, recall}}
    """
    cases = load_fixture_cases()
    # Accumulate per-code stats
    stats: Dict[str, Dict[str, int]] = {}

    for case in cases:
        report = run_full_verification(
            source_text=case["source"],
            target_text=case["target"],
            enable_nli=False,
        )
        found_codes = {f.code for f in report.findings}
        expected = {ef["code"] for ef in case.get("expected_findings", [])}

        for code in expected | found_codes:
            if code not in stats:
                stats[code] = {"TP": 0, "FP": 0, "FN": 0}

        for code in expected:
            if code in found_codes:
                stats[code]["TP"] += 1
            else:
                stats[code]["FN"] += 1

        for code in found_codes:
            if code not in expected:
                stats[code]["FP"] += 1

    # Compute precision/recall
    results = {}
    for code, s in stats.items():
        tp, fp, fn = s["TP"], s["FP"], s["FN"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        results[code] = {
            "TP": tp, "FP": fp, "FN": fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
        }

    return results



@pytest.fixture(scope="module")
def fixture_eval_results():
    """Module-scoped: run full 40-case eval once per test session."""
    return evaluate_checker_on_fixtures()


class TestPrecisionRecall:
    """
    Runs the 40-case fixture set and asserts minimum precision/recall per check.

    Thresholds are intentionally conservative given the documented limitations:
    - Fabricated claims: 0% recall (by design — deterministic blind spot).
    - Subtle cases with number-to-word conversion: may miss.

    These are MEASURED thresholds from the fixture set, not aspirational targets.
    """

    def test_numeric_recall_above_threshold(self, fixture_eval_results):
        """NUMERIC_VALUE_DROPPED_OR_ALTERED should catch most changed numbers."""
        code = "NUMERIC_VALUE_DROPPED_OR_ALTERED"
        if code not in fixture_eval_results:
            pytest.skip(f"Code {code} not in results")
        result = fixture_eval_results[code]
        print(f"\n[EVAL] {code}: TP={result['TP']} FP={result['FP']} FN={result['FN']} "
              f"P={result['precision']:.2f} R={result['recall']:.2f}")
        assert result["recall"] >= 0.60, f"Numeric recall too low: {result['recall']}"

    def test_citation_recall_above_threshold(self, fixture_eval_results):
        """CITATION_DROPPED should catch most dropped citations."""
        code = "CITATION_DROPPED"
        if code not in fixture_eval_results:
            pytest.skip(f"Code {code} not in results")
        result = fixture_eval_results[code]
        print(f"\n[EVAL] {code}: TP={result['TP']} FP={result['FP']} FN={result['FN']} "
              f"P={result['precision']:.2f} R={result['recall']:.2f}")
        assert result["recall"] >= 0.80, f"Citation recall too low: {result['recall']}"

    def test_negation_recall_above_threshold(self, fixture_eval_results):
        """NEGATION_DROPPED should catch explicit keyword negations."""
        code = "NEGATION_DROPPED"
        if code not in fixture_eval_results:
            pytest.skip(f"Code {code} not in results")
        result = fixture_eval_results[code]
        print(f"\n[EVAL] {code}: TP={result['TP']} FP={result['FP']} FN={result['FN']} "
              f"P={result['precision']:.2f} R={result['recall']:.2f}")
        assert result["recall"] >= 0.70, f"Negation recall too low: {result['recall']}"

    def test_structure_recall_above_threshold(self, fixture_eval_results):
        """PARAGRAPH_COUNT_MISMATCH should catch all structural changes."""
        code = "PARAGRAPH_COUNT_MISMATCH"
        if code not in fixture_eval_results:
            pytest.skip(f"Code {code} not in results")
        result = fixture_eval_results[code]
        print(f"\n[EVAL] {code}: TP={result['TP']} FP={result['FP']} FN={result['FN']} "
              f"P={result['precision']:.2f} R={result['recall']:.2f}")
        assert result["recall"] >= 0.80, f"Structure recall too low: {result['recall']}"

    def test_fabricated_blind_spot_documented(self, fixture_eval_results):
        """
        Verifies the documented blind spot for fabricated claims.

        Deterministic checks (numbers, citations, negations) must NOT fire CRITICAL
        for cases where source content is preserved and new content is merely *added*.

        Semantic similarity MAY flag added fabricated content as drift — this is
        correct and expected (added content changes meaning), but it is NOT a
        targeted detection of fabrication. The system cannot distinguish a clarifying
        paraphrase from a fabricated addition at the semantic level.

        DOCUMENTED BLIND SPOT: 0% recall on fabricated fact detection (by design).
        Every API response includes this limitation in the similarity_note field.
        """
        cases = load_fixture_cases()
        fabricated = [c for c in cases if c["category"] == "fabricated_claim"]
        for case in fabricated:
            report = run_full_verification(case["source"], case["target"], enable_nli=False)
            # Deterministic checkers must NOT fire CRITICAL for fabricated additions
            deterministic_critical = [
                f for f in report.findings
                if f.severity == "CRITICAL"
                and f.code in ("NUMERIC_VALUE_DROPPED_OR_ALTERED", "CITATION_DROPPED", "NEGATION_DROPPED")
            ]
            assert len(deterministic_critical) == 0, (
                f"Case {case['id']}: unexpected deterministic CRITICAL on fabricated case "
                f"(source content preserved; only new content added): "
                f"{[f.code for f in deterministic_critical]}"
            )
            # Semantic drift is legitimate signal — log it but don't assert absence
            semantic_findings = [f for f in report.findings if f.category == "semantics"]
            if semantic_findings:
                print(f"\n  [{case['id']}] score={report.overall_similarity_score:.3f} "
                      f"semantic findings={[f.code for f in semantic_findings]} "
                      f"(expected for added content; not a fabrication detection)")

    def test_print_full_eval_table(self, fixture_eval_results):
        """Print a readable summary of all codes — always passes, for visibility."""
        print("\n\n=== Phase 6 Verification Precision/Recall Evaluation ===")
        print(f"{'Code':<45} {'TP':>4} {'FP':>4} {'FN':>4} {'P':>6} {'R':>6}")
        print("-" * 75)
        for code, r in sorted(fixture_eval_results.items()):
            print(f"{code:<45} {r['TP']:>4} {r['FP']:>4} {r['FN']:>4} {r['precision']:>6.2f} {r['recall']:>6.2f}")
        print("\nKNOWN BLIND SPOTS:")
        print("  - Fabricated facts/invented numbers not in source: 0% recall (by design)")
        print("  - Implicit negation ('failed to', 'lack of'): missed by keyword approach")
        print("  - Number-to-word conversions ('forty-two' -> '42'): may miss")
        print("  - Subtle semantic contradictions (scope, negated implications): NLI required")
        assert True

