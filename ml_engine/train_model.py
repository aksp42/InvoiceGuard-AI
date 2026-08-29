"""
Train the Isolation Forest model and persist model.pkl / scaler.pkl.

Usage:
    python -m ml_engine.train_model --data database/sample_invoices.csv
"""
import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ml_engine.feature_engineering import FEATURE_COLUMNS, build_features
from ml_engine.anomaly_detection import AnomalyDetector

BASE_DIR = Path(__file__).resolve().parent.parent


def train(data_path: str, model_path: Path, scaler_path: Path) -> None:
    df = pd.read_csv(data_path)
    if len(df) < 2:
        raise SystemExit("Need at least 2 rows to train the Isolation Forest.")

    features = build_features(df)
    X = features[FEATURE_COLUMNS].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = AnomalyDetector()
    # Fit on the scaled features using the underlying estimator directly
    model.model.fit(X_scaled)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model.model, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"Saved model  -> {model_path}")
    print(f"Saved scaler -> {scaler_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the invoice anomaly model")
    parser.add_argument("--data", default=str(BASE_DIR / "database" / "sample_invoices.csv"))
    parser.add_argument("--model", default=str(BASE_DIR / "ml_engine" / "model.pkl"))
    parser.add_argument("--scaler", default=str(BASE_DIR / "ml_engine" / "scaler.pkl"))
    args = parser.parse_args()
    train(args.data, Path(args.model), Path(args.scaler))