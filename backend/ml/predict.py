"""
Prediction module — wraps the trained XGBoost model as a singleton.

Usage:
    from backend.ml.predict import predictor
    result = predictor.predict(flow_features_dict)
"""

import os
import logging

import pandas as pd
import joblib

from backend.config import MODEL_PATH, FEATURE_COLUMNS_PATH

logger = logging.getLogger(__name__)


class IDSPredictor:
    """Loads the trained IDS model and provides a ``predict`` method."""

    def __init__(self):
        self.model = None
        self.feature_columns = None
        self._loaded = False
        self._load_model()

    def _load_model(self):
        try:
            if not os.path.exists(MODEL_PATH):
                logger.warning(
                    "Model file not found at '%s'. "
                    "Run 'python -m backend.ml.train' first.",
                    MODEL_PATH,
                )
                return
            if not os.path.exists(FEATURE_COLUMNS_PATH):
                logger.warning(
                    "Feature columns file not found at '%s'. "
                    "Run 'python -m backend.ml.train' first.",
                    FEATURE_COLUMNS_PATH,
                )
                return

            self.model = joblib.load(MODEL_PATH)
            self.feature_columns = joblib.load(FEATURE_COLUMNS_PATH)
            self._loaded = True
            logger.info("IDS model loaded successfully (%d features).", len(self.feature_columns))
        except Exception as exc:
            logger.error("Failed to load IDS model: %s", exc)
            self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def predict(self, flow_features: dict) -> dict:
        """
        Predict whether a flow is NORMAL or MALICIOUS.

        Parameters
        ----------
        flow_features : dict
            Feature dict produced by ``FlowData.compute_features()``.

        Returns
        -------
        dict with keys ``label``, ``confidence``, ``raw_prediction``.
        """
        if not self._loaded:
            # Fallback — treat everything as normal when no model is loaded
            return {
                "label": "NORMAL",
                "confidence": 0.0,
                "raw_prediction": 0,
            }

        # Build a single-row DataFrame
        df = pd.DataFrame([flow_features])

        # Align columns to training order — missing cols filled with 0
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0

        df = df[self.feature_columns]

        # Replace any residual NaN/Inf
        df.fillna(0, inplace=True)
        df.replace([float("inf"), float("-inf")], 0, inplace=True)

        raw_pred = int(self.model.predict(df)[0])
        proba = self.model.predict_proba(df)[0]

        # Confidence = probability of the predicted class
        confidence = round(float(proba[raw_pred]), 4)

        label = "MALICIOUS" if raw_pred == 1 else "NORMAL"

        return {
            "label": label,
            "confidence": confidence,
            "raw_prediction": raw_pred,
        }

    def predict_batch(self, df: pd.DataFrame) -> dict:
        if not self._loaded:
            return {"total": len(df), "malicious": 0, "normal": len(df)}
        
        # Align columns to training order
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0

        df_aligned = df[self.feature_columns].copy()
        
        df_aligned.fillna(0, inplace=True)
        df_aligned.replace([float("inf"), float("-inf")], 0, inplace=True)

        preds = self.model.predict(df_aligned)
        
        malicious_count = int(sum(preds == 1))
        total = len(df)
        
        return {
            "total": total,
            "malicious": malicious_count,
            "normal": total - malicious_count
        }

# Singleton instance — importable from anywhere
predictor = IDSPredictor()
