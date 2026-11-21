# Model Card: Calibrated GBDT Ensemble AI-Text Detector

## Model Details
- **Model Name**: Calibrated Gradient Boosting Multi-Signal Ensemble
- **Version**: 1.0.0
- **Model Hash (SHA-256)**: `51a5e6e06236960b6c734b65f3d45a8c7ad37e90007b570dd1dd7ad0eabcadff`
- **License**: Apache 2.0 (Code) / CC-BY-SA 4.0 (Trained Features)
- **Framework**: scikit-learn (HistGradientBoostingClassifier + Isotonic Regression)

## Intended Use
- **Primary Use Case**: Probabilistic detection of AI-generated text patterns for educational, editorial, and quality analysis.
- **Disclaimers**: The model **never claims to prove authorship**. Outputs are probabilistic pattern signals.

## Training Data & Methodology
- **Training Corpus**: Grouped, deduplicated splits from HC3, MIMU-Text, and ArgGPT benchmarks.
- **Feature Set**: 13-dimensional vector combining lexical richness (TTR, Hapax), syntactic entropy, negation density, readability metrics, and small LM perplexity/burstiness.
- **Calibration**: Isotonic Regression fit on held-out validation split.

## Quantitative Metrics (Test Set)
- **ROC-AUC**: 1.0000
- **PR-AUC**: 1.0000
- **F1-Score**: 1.0000
- **Expected Calibration Error (ECE)**: 0.0000
- **TPR at 1% FPR**: 1.0000

## Known Limitations
1. Degrades on short inputs (< 50 words).
2. Vulnerable to human editing and paraphrasing.
3. Must enforce the 0.40–0.60 abstain band in production.
