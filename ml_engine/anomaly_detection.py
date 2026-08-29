"""
Anomaly detection wrapper (Isolation Forest).

Produces a 0-100 risk-like score per sample (higher = more anomalous) and a
boolean anomaly flag, independent of the rule-based checks.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ml_engine.feature_engineering import FEATURE_COLUMNS, build_features


class AnomalyDetector:
    def __init__(self, contamination: float = 0.2, n_estimators: int = 200, random_state: int = 42):
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=min(contamination, 0.4),
            random_state=random_state,
        )

    def fit(self, df: pd.DataFrame) -> "AnomalyDetector":
        X = build_features(df)[FEATURE_COLUMNS].values
        self.model.fit(X)
        return self

    def transform(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Returns (risk_scores 0-100, anomaly_flags)."""
        X = build_features(df)[FEATURE_COLUMNS].values
        raw_scores = self.model.decision_function(X)
        normalized = (raw_scores.max() - raw_scores) / (raw_scores.max() - raw_scores.min() + 1e-9)
        risk_score = np.round(normalized * 100, 1)
        flags = self.model.predict(X) == -1
        return risk_score, flags

    def fit_predict(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        self.fit(df)
        return self.transform(df)