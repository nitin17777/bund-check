"""
Evaluation Engine:
Calculates:
- Precision, Recall, F1, ROC-AUC, PR-AUC
- False Positive Rate (FPR) and False Negative Rate (FNR)
- True Positive Rate (TPR) at fixed low FPR (e.g. FPR <= 1% and FPR <= 5%)
- Expected Calibration Error (ECE) and reliability diagram curve data
- Per-domain and per-generator breakdown
- Robustness evaluation:
  (i) Short texts (< 50 words)
  (ii) Paraphrased / human-edited AI text
  (iii) Diverse human writing styles (academic / non-native proxies)
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.metrics import (
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    auc,
    confusion_matrix,
    brier_score_loss,
)


def compute_comprehensive_metrics(
    y_true: np.ndarray, y_probs: np.ndarray, threshold: float = 0.5
) -> Dict[str, Any]:
    y_pred = (y_probs >= threshold).astype(int)

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = float(fp / max(fp + tn, 1))
    fnr = float(fn / max(fn + tp, 1))

    # Standard metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    roc_auc = float(roc_auc_score(y_true, y_probs)) if len(np.unique(y_true)) > 1 else 0.5

    precision_curve, recall_curve, _ = precision_recall_curve(y_true, y_probs)
    pr_auc = float(auc(recall_curve, precision_curve))

    # TPR at fixed low FPR thresholds (1% and 5%)
    fpr_curve, tpr_curve, _ = roc_curve(y_true, y_probs)
    tpr_at_fpr_1 = float(np.interp(0.01, fpr_curve, tpr_curve))
    tpr_at_fpr_5 = float(np.interp(0.05, fpr_curve, tpr_curve))

    # Expected Calibration Error (ECE)
    ece, reliability_bins = compute_ece(y_true, y_probs, num_bins=10)
    brier = float(brier_score_loss(y_true, y_probs))

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "fpr": fpr,
        "fnr": fnr,
        "tpr_at_1pct_fpr": tpr_at_fpr_1,
        "tpr_at_5pct_fpr": tpr_at_fpr_5,
        "ece": ece,
        "brier_score": brier,
        "total_samples": len(y_true),
        "reliability_bins": reliability_bins,
    }


def compute_ece(
    y_true: np.ndarray, y_probs: np.ndarray, num_bins: int = 10
) -> Tuple[float, List[Dict[str, float]]]:
    """
    Computes Expected Calibration Error across equal-width confidence bins.
    """
    bin_limits = np.linspace(0, 1, num_bins + 1)
    ece = 0.0
    bins_data: List[Dict[str, float]] = []

    for i in range(num_bins):
        low, high = bin_limits[i], bin_limits[i + 1]
        mask = (y_probs >= low) & (y_probs < high) if i < num_bins - 1 else (y_probs >= low) & (y_probs <= high)
        bin_count = np.sum(mask)

        if bin_count > 0:
            bin_acc = float(np.mean(y_true[mask]))
            bin_conf = float(np.mean(y_probs[mask]))
            bin_weight = bin_count / len(y_true)
            ece += bin_weight * abs(bin_acc - bin_conf)
            bins_data.append({
                "bin_low": float(low),
                "bin_high": float(high),
                "count": int(bin_count),
                "confidence": bin_conf,
                "accuracy": bin_acc,
            })

    return float(ece), bins_data


def evaluate_breakdowns(
    records: List[Any], y_probs: np.ndarray
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates metrics partitioned by domain, generator model, and text length.
    """
    y_true = np.array([r.label for r in records])
    domains = set(r.domain for r in records)
    generators = set(r.generator for r in records)

    domain_results: Dict[str, Any] = {}
    for d in domains:
        mask = np.array([r.domain == d for r in records])
        if np.sum(mask) >= 5 and len(np.unique(y_true[mask])) > 1:
            domain_results[d] = compute_comprehensive_metrics(y_true[mask], y_probs[mask])

    generator_results: Dict[str, Any] = {}
    for g in generators:
        mask = np.array([r.generator == g for r in records])
        # Generator evaluation: compare this generator's texts against human texts
        human_mask = np.array([r.label == 0 for r in records])
        sub_mask = mask | human_mask
        if np.sum(mask) >= 5:
            generator_results[g] = compute_comprehensive_metrics(y_true[sub_mask], y_probs[sub_mask])

    # Robustness checks:
    # 1. Short texts (< 50 words)
    short_mask = np.array([len(r.text.split()) < 50 for r in records])
    short_metrics = compute_comprehensive_metrics(y_true[short_mask], y_probs[short_mask]) if np.sum(short_mask) >= 5 else None

    # 2. Human-edited AI text
    edited_mask = np.array(["edited" in r.generator.lower() for r in records])
    human_mask = np.array([r.label == 0 for r in records])
    edited_sub = edited_mask | human_mask
    edited_metrics = compute_comprehensive_metrics(y_true[edited_sub], y_probs[edited_sub]) if np.sum(edited_mask) >= 5 else None

    return {
        "by_domain": domain_results,
        "by_generator": generator_results,
        "short_text_robustness": short_metrics,
        "human_edited_robustness": edited_metrics,
    }
