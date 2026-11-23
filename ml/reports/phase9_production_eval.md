# Phase 9: Production Path Detector Evaluation

**Evaluation Date**: 2026-11-23  
**Inference Path**: `backend.app.services.detection.detector.run_detection_pipeline`  
**Model Artifact**: `ml/models/artifacts/gbdt_calibrated_ensemble.joblib`  
**Hardware**: RTX 2050 (4 GB VRAM) / 24 GB RAM — inference on CPU  
**Calibration**: Isotonic Regression (fit on held-out validation split during training)

> [!IMPORTANT]
> **Test set is SYNTHETIC** (N=14). No held-out real-world dataset was found in `ml/data/`
> or `ml/datasets/`. All samples were constructed to cover canonical human prose (long, varied,
> idiomatic), canonical AI-style prose (uniform, low burstiness), short-text edge cases (<50 words),
> and human-edited AI text proxies. Numbers below reflect performance on this synthetic corpus
> **only**; they cannot be directly extrapolated to real-world deployment distributions.

---

## 1. Overall Metrics — Production Threshold (≥ 0.60 → SYNTHETIC_INDICATIVE)

| Metric | Value (threshold=0.60) | Value (threshold=0.50) |
|--------|------------------------|------------------------|
| **Accuracy** | **0.4286** | 0.3571 |
| **Precision** | **0.5000** | 0.4444 |
| **Recall** | **0.5000** | 0.5000 |
| **F1-Score** | **0.5000** | 0.4706 |
| **ROC-AUC** | **0.3646** | — |
| **PR-AUC** | **0.5908** | — |
| **ECE (Expected Calibration Error)** | **0.5546** | — |
| **Brier Score** | **0.5023** | — |
| **FPR (False Positive Rate)** | **0.6667** | 0.8333 |
| **FNR (False Negative Rate)** | **0.5000** | 0.5000 |
| **TPR @ 1% FPR** | **0.0056** | — |
| **TPR @ 5% FPR** | **0.0281** | — |
| **Total Samples** | 14 | 14 |

---

## 2. Per-Domain Breakdown

| Domain | Precision | Recall | F1 | ROC-AUC | ECE | N |
|--------|-----------|--------|----|---------|-----|---|
| academic | 1.000 | 0.333 | 0.500 | 1.000 | 0.384 | 4 |
| essay | 0.667 | 1.000 | 0.800 | 0.625 | 0.365 | 4 |
| journalism | 0.000 | 0.000 | 0.000 | 0.000 | 0.923 | 3 |
| technical | 0.500 | 0.500 | 0.500 | 0.250 | 0.667 | 3 |

---

## 3. Per-Generator Breakdown

| Generator | Precision | Recall | F1 | FPR | N |
|-----------|-----------|--------|----|-----|---|
| gpt-style | 0.200 | 0.200 | 0.200 | 0.667 | 11 |
| gpt-style_short | 0.200 | 1.000 | 0.333 | 0.667 | 7 |
| human_edited_ai | 0.333 | 1.000 | 0.500 | 0.667 | 8 |

---

## 4. Robustness Checks

### 4.1 Short Text (<50 words)

- Precision: 1.0000
- Recall: 1.0000
- F1: 1.0000
- N: 2

> [!WARNING]
> Short text performance is unreliable. The production pipeline explicitly flags texts
> under 50 words with `UNRELIABLE_VERY_SHORT_TEXT`. Numbers above are for reference only.

### 4.2 Human-Edited AI Text

- Precision: 0.3333
- Recall: 1.0000
- F1: 0.5000
- N: 8

> [!NOTE]
> Human-edited AI text is the hardest category. Prior research (and the existing
> `detection_eval.md` report) documents up to 28% recall drop on heavily edited AI text.
> The synthetic proxies here are mildly edited; real production edited text would likely
> perform worse.

---

## 5. Per-Sample Detail

| # | Label | Generator | Domain | Words | Prob | Band | Flag |
|---|-------|-----------|--------|-------|------|------|------|
| 0 | Human | human | journalism | 126 | 1.0000 | SYNTHETIC_INDICATIVE | LOW_RELIABILITY_SHORT_TEXT |
| 1 | Human | human | essay | 149 | 1.0000 | SYNTHETIC_INDICATIVE | LOW_RELIABILITY_SHORT_TEXT |
| 2 | Human | human | academic | 135 | 0.0000 | HUMAN_TYPICAL | LOW_RELIABILITY_SHORT_TEXT |
| 3 | Human | human | journalism | 132 | 1.0000 | SYNTHETIC_INDICATIVE | LOW_RELIABILITY_SHORT_TEXT |
| 4 | Human | human | technical | 119 | 1.0000 | SYNTHETIC_INDICATIVE | LOW_RELIABILITY_SHORT_TEXT |
| 5 | AI | gpt-style | academic | 126 | 0.2322 | HUMAN_TYPICAL | LOW_RELIABILITY_SHORT_TEXT |
| 6 | AI | gpt-style | essay | 132 | 0.9497 | SYNTHETIC_INDICATIVE | LOW_RELIABILITY_SHORT_TEXT |
| 7 | AI | gpt-style | technical | 139 | 0.0000 | HUMAN_TYPICAL | LOW_RELIABILITY_SHORT_TEXT |
| 8 | AI | gpt-style | journalism | 127 | 0.2322 | HUMAN_TYPICAL | LOW_RELIABILITY_SHORT_TEXT |
| 9 | AI | gpt-style | academic | 130 | 0.2322 | HUMAN_TYPICAL | LOW_RELIABILITY_SHORT_TEXT |
| 10 | Human | human_short | essay | 28 | 0.5116 | INCONCLUSIVE | UNRELIABLE_VERY_SHORT_TEXT |
| 11 | AI | gpt-style_short | technical | 22 | 1.0000 | SYNTHETIC_INDICATIVE | UNRELIABLE_VERY_SHORT_TEXT |
| 12 | AI | human_edited_ai | academic | 114 | 1.0000 | SYNTHETIC_INDICATIVE | LOW_RELIABILITY_SHORT_TEXT |
| 13 | AI | human_edited_ai | essay | 120 | 1.0000 | SYNTHETIC_INDICATIVE | LOW_RELIABILITY_SHORT_TEXT |

---

## 6. Limitations

> [!CAUTION]
> The following limitations apply to all results in this report and to the production detector.
> Users and developers MUST read and understand these limitations before using or citing detector outputs.

### 6.1 Training / Test Distribution Mismatch
- **This report uses a synthetic test set.** The model artifact (`gbdt_calibrated_ensemble.joblib`)
  was trained and calibrated on a held-out split of the development corpus. This evaluation script
  does not have access to that corpus and constructs a small synthetic set instead.
- Metrics on the synthetic set reflect the model's ability to discriminate between *prototypical*
  human prose and *prototypical* AI prose. Real-world text is messier, more varied, and often
  falls somewhere in between.
- **Do not use the numbers in this report as a headline accuracy claim for real-world performance.**
  Refer to `ml/reports/detection_eval.md` for the training-time evaluation against the actual
  development corpus.

### 6.2 Known Failure Modes
1. **Human-Edited AI Text**: The detector degrades significantly when AI-generated text undergoes
   human stylistic revision. Prior evaluation documents recall drops of up to 28% on this category.
2. **Short Text (<50 words)**: Sentence perplexity variance cannot be computed reliably on very short
   texts. The production pipeline flags these as `UNRELIABLE_VERY_SHORT_TEXT` and explicitly widens
   the uncertainty interval.
3. **Domain Shift (Legal/Technical/Non-Native English)**: Formal technical and legal prose, and
   non-native English writing, exhibit naturally lower lexical entropy and flatter perplexity
   distributions. These features mimic AI-style signals and may elevate false-positive rates.
4. **Out-of-Distribution Generators**: Models unseen during training (e.g., new proprietary LLMs)
   may produce stylistic patterns not covered by the GBDT's training distribution.
5. **Low-Vocabulary Domains**: Formulaic genres (legal disclaimers, software changelogs, meeting
   minutes) may systematically trigger elevated synthetic confidence regardless of actual authorship.

### 6.3 Abstain Band Rationale
- The production pipeline abstains from classification when `synthetic_pattern_confidence ∈ [0.40, 0.60]`.
- This band is configured via `ABSTAIN_LOWER_THRESHOLD` / `ABSTAIN_UPPER_THRESHOLD` in
  `backend/app/core/config.py` and was set based on calibration reliability curves.
- **Rationale**: The model's reliability in this region is insufficient to make a directional claim.
  Forcing a binary decision in this band would inflate both false positives and false negatives.
  The abstain design is a conservative, honest choice — not a limitation to be engineered away.

### 6.4 What the Model CANNOT Do
- **Cannot prove AI authorship**: A high `synthetic_pattern_confidence` score indicates statistical
  alignment with machine text patterns. It does not constitute proof that a specific AI system
  generated the text, nor does it disprove human authorship.
- **Cannot attribute to a specific AI model**: The detector is a binary/ordinal classifier;
  it cannot identify which LLM generated a text.
- **Cannot detect lightly paraphrased AI text**: Translation round-trips, synonym substitution,
  or sentence reordering significantly degrade detection.
- **Cannot evaluate document fragments reliably**: Paragraph-level and sentence-level scores are
  explicitly labelled as *exploratory local variance indicators* and do not constitute independent
  attribution evidence.
- **Cannot guarantee zero false positives on any real corpus**: The model is calibrated to minimize
  expected calibration error on its training distribution; FPR on out-of-distribution corpora
  is uncharacterised.

---

## 7. Comparison with Phase 3 Training-Time Report

| Metric | Training-Time (detection_eval.md) | Phase 9 Production Path (synthetic) |
|--------|-----------------------------------|--------------------------------------|
| F1 | 1.000 (GBDT) | *see Section 1* |
| ECE | 0.000 (GBDT) | *see Section 1* |
| Test N | unreported | 14 (synthetic) |

> [!NOTE]
> The training-time report shows perfect scores (F1=1.000, ECE=0.000) on the development
> corpus. This is consistent with a small, well-separated synthetic training set where the
> stylometric signals are unambiguous. These numbers should **not** be interpreted as
> production accuracy on real-world documents. Real-world performance on ambiguous or
> mixed-authorship text will be substantially lower.

---

*Report generated by `scratch/eval_production_path.py` on 2026-11-23.*  
*Test corpus: synthetic, N=14.*