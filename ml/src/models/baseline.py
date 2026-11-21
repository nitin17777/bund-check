"""
Baseline Model Trainers:
- Logistic Regression (Calibrated with StandardScaler)
- Gradient Boosting Classifier (Histogram-based GBDT)
- Ensemble combination
- Kaggle / Colab exportable training script generation
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV


class FeatureClassifierPipeline:
    def __init__(self, model_type: str = "gradient_boosting", calibrate: bool = True):
        self.model_type = model_type
        self.calibrate = calibrate
        self.scaler = StandardScaler()
        
        if model_type == "logistic_regression":
            self.base_model = LogisticRegression(max_iter=1000, random_state=42)
        elif model_type == "gradient_boosting":
            self.base_model = HistGradientBoostingClassifier(random_state=42, max_iter=100)
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        self.calibrated_model = None

    def fit(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray):
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Fit base model on training data
        self.base_model.fit(X_train_scaled, y_train)

        # Calibration on validation set strictly (Isotonic or Platt scaling)
        if self.calibrate:
            # We fit isotonic or sigmoid calibrator on validation probabilities
            val_probs = self.base_model.predict_proba(X_val_scaled)[:, 1]
            from sklearn.isotonic import IsotonicRegression
            self.calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            self.calibrator.fit(val_probs, y_val)
        else:
            self.calibrator = None

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self.scaler.transform(X)
        raw_probs = self.base_model.predict_proba(X_scaled)[:, 1]
        if self.calibrate and self.calibrator is not None:
            cal_probs = self.calibrator.predict(raw_probs)
            # Clip between 0 and 1
            cal_probs = np.clip(cal_probs, 0.0, 1.0)
            return np.vstack([1.0 - cal_probs, cal_probs]).T
        return self.base_model.predict_proba(X_scaled)

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(int)

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)

    @staticmethod
    def load(filepath: str) -> "FeatureClassifierPipeline":
        return joblib.load(filepath)
