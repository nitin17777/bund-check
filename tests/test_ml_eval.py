"""
Unit and Integration Tests for Phase 3:
- Data schema, deduplication (MinHash), prompt-grouped splits, split leakage validation
- Feature extraction (stylometrics, small LM fallback/feature vector dimension and finiteness)
- Feature classifier pipeline (training, calibration on validation set, predictions)
- Evaluation metrics (ROC-AUC, PR-AUC, ECE, TPR at low FPR)
"""

import pytest
import numpy as np
import tempfile
import os
from ml.src.data.schema import (
    DataRecord,
    deduplicate_records,
    split_grouped_dataset,
    assert_no_split_leakage
)
from ml.src.features.extractor import (
    extract_stylometric_features,
    extract_combined_features,
    cache_features_to_disk,
    load_cached_features
)
from ml.src.models.baseline import FeatureClassifierPipeline
from ml.src.eval.metrics import (
    compute_comprehensive_metrics,
    compute_ece
)


def test_data_record_and_minhash_deduplication():
    # Identical texts
    rec1 = DataRecord(
        text="The quick brown fox jumps over the lazy dog repeatedly in the forest.",
        label=0,
        source="human_test",
        domain="general",
        generator="human",
        prompt_id="p1"
    )
    rec2 = DataRecord(
        text="The quick brown fox jumps over the lazy dog repeatedly in the forest.",
        label=0,
        source="human_test",
        domain="general",
        generator="human",
        prompt_id="p2"
    )
    # Distinct text
    rec3 = DataRecord(
        text="Artificial intelligence systems utilize statistical optimization for language tasks.",
        label=1,
        source="ai_test",
        domain="tech",
        generator="gpt4",
        prompt_id="p3"
    )

    records = [rec1, rec2, rec3]
    deduped = deduplicate_records(records, threshold=0.8)
    assert len(deduped) == 2
    assert deduped[0].prompt_id == "p1"
    assert deduped[1].prompt_id == "p3"


def test_split_grouped_dataset_and_leakage_assertion():
    records = []
    # Create 10 prompts, 4 records each
    for p in range(10):
        prompt_id = f"prompt_{p}"
        for i in range(4):
            records.append(
                DataRecord(
                    text=f"Text for prompt {p} item {i} discussing machine learning topic {p}.",
                    label=i % 2,
                    source="synthetic_test",
                    domain="ml",
                    generator="gpt3" if i % 2 == 1 else "human",
                    prompt_id=prompt_id
                )
            )

    train, val, test = split_grouped_dataset(records, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, random_state=42)
    
    assert len(train) > 0
    assert len(val) > 0
    assert len(test) > 0
    assert len(train) + len(val) + len(test) == len(records)

    # Validate leakage passes
    assert_no_split_leakage(train, val, test)

    # Inject deliberate leakage and verify assertion failure
    leaked_record = DataRecord(
        text="Leaked prompt sample",
        label=1,
        source="leak",
        domain="leak",
        generator="leak",
        prompt_id=train[0].prompt_id  # Re-use prompt from train
    )
    with pytest.raises(ValueError, match="Leakage detected"):
        assert_no_split_leakage(train, val, [leaked_record])


def test_stylometric_features():
    text = (
        "Furthermore, artificial intelligence algorithms utilize mathematical optimization. "
        "However, they cannot verify semantic truth without grounded external references. "
        "Does this imply automated detection requires calibrated thresholds? Indeed, it does."
    )
    feats = extract_stylometric_features(text)
    
    assert feats["type_token_ratio"] > 0.0
    assert feats["sentence_length_mean"] > 0.0
    assert feats["flesch_reading_ease"] != 0.0
    assert feats["negation_density"] > 0.0
    assert feats["function_word_ratio"] > 0.0

    # Test empty text edge case
    empty_feats = extract_stylometric_features("   ")
    assert empty_feats["type_token_ratio"] == 0.0
    assert empty_feats["sentence_length_mean"] == 0.0


def test_feature_vector_dimension_and_caching():
    text = "The system evaluates probabilistic features across multiple linguistic dimensions."
    vec = extract_combined_features(text)
    
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (13,)
    assert not np.isnan(vec).any()
    assert not np.isinf(vec).any()

    # Test caching
    with tempfile.TemporaryDirectory() as tmp_dir:
        cache_path = os.path.join(tmp_dir, "test_features.joblib")
        matrix = np.array([vec, vec])
        labels = np.array([0, 1])
        cache_features_to_disk(matrix, labels, cache_path)

        loaded_X, loaded_y = load_cached_features(cache_path)
        assert np.allclose(matrix, loaded_X)
        assert np.array_equal(labels, loaded_y)


def test_classifier_pipeline_and_isotonic_calibration():
    np.random.seed(42)
    # Generate synthetic feature sets
    n_train = 60
    n_val = 20
    n_test = 20
    n_features = 13

    # Human-typical features (class 0)
    X0 = np.random.normal(loc=0.0, scale=1.0, size=(n_train + n_val + n_test, n_features))
    # AI-indicative features (class 1)
    X1 = np.random.normal(loc=2.0, scale=1.0, size=(n_train + n_val + n_test, n_features))

    X_all = np.vstack([X0, X1])
    y_all = np.array([0] * len(X0) + [1] * len(X1))

    indices = np.random.permutation(len(X_all))
    X_all = X_all[indices]
    y_all = y_all[indices]

    X_train, y_train = X_all[:80], y_all[:80]
    X_val, y_val = X_all[80:110], y_all[80:110]
    X_test, y_test = X_all[110:], y_all[110:]

    for model_type in ["logistic_regression", "gradient_boosting"]:
        pipeline = FeatureClassifierPipeline(model_type=model_type, calibrate=True)
        pipeline.fit(X_train, y_train, X_val, y_val)

        probs = pipeline.predict_proba(X_test)
        assert probs.shape == (len(X_test), 2)
        assert np.all(probs >= 0.0)
        assert np.all(probs <= 1.0)
        np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-5)

        preds = pipeline.predict(X_test, threshold=0.5)
        assert preds.shape == (len(X_test),)
        assert set(preds).issubset({0, 1})


def test_metrics_computation():
    y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.15, 0.35, 0.45, 0.65, 0.8, 0.85, 0.9, 0.95])

    metrics = compute_comprehensive_metrics(y_true, y_prob, threshold=0.5)
    
    assert metrics["roc_auc"] == 1.0
    assert metrics["pr_auc"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["fpr"] == 0.0
    assert metrics["fnr"] == 0.0
    assert metrics["tpr_at_1pct_fpr"] == 1.0
    assert metrics["tpr_at_5pct_fpr"] == 1.0

    ece, bins = compute_ece(y_true, y_prob, num_bins=5)
    assert 0.0 <= ece <= 1.0
    assert len(bins) == 5
