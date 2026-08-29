"""
Scoring entry point used by the backend.

Loads a pre-trained model + scaler if available (ml_engine/model.pkl,
ml_engine/scaler.pkl). Falls back to fitting on the incoming batch so the
project still works before any training run.
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ml_engine.feature_engineering import FEATURE_COLUMNS, build_features

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.pkl"
SCALER_PATH = BASE_DIR / "scaler.pkl"


def _load_or_fit(df: pd.DataFrame):
    """Returns (model, scaler). Tries persisted artefacts, else fits on the batch."""
    if MODEL_PATH.exists() and SCALER_PATH.exists():
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
    else:
        X = build_features(df)[FEATURE_COLUMNS].values
        model = IsolationForest(n_estimators=200, contamination=0.2, random_state=42)
        scaler = StandardScaler()
        model.fit(scaler.fit_transform(X))
    return model, scaler


def score_invoices(df: pd.DataFrame) -> pd.DataFrame:
    """Adds 'ml_risk_score' (0-100) and 'ml_flag' (bool) columns."""
    if len(df) < 2:
        result = df.copy()
        result["ml_risk_score"] = 0.0
        result["ml_flag"] = False
        return result

    X = build_features(df)[FEATURE_COLUMNS].values
    model, scaler = _load_or_fit(df)
    X_scaled = scaler.transform(X)

    raw_scores = model.decision_function(X_scaled)
    normalized = (raw_scores.max() - raw_scores) / (raw_scores.max() - raw_scores.min() + 1e-9)
    risk_score = (normalized * 100).round(1)
    flags = model.predict(X_scaled) == -1

    result = df.copy()
    result["ml_risk_score"] = risk_score
    result["ml_flag"] = flags
    return result