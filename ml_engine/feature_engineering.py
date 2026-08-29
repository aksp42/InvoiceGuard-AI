"""
Feature engineering for anomaly detection.

Builds the numeric feature matrix used by the Isolation Forest:
  - quantity
  - unit_price
  - total_amount
  - vendor_avg_price_ratio (unit price vs that vendor's historical average)
"""
import numpy as np
import pandas as pd

FEATURE_COLUMNS = ["quantity", "unit_price", "total_amount", "vendor_avg_price_ratio"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    features = df.copy()
    features["quantity"] = pd.to_numeric(features["quantity"], errors="coerce")
    features["unit_price"] = pd.to_numeric(features["unit_price"], errors="coerce")
    features["total_amount"] = pd.to_numeric(features["total_amount"], errors="coerce")

    vendor_avg = features.groupby("vendor_name")["unit_price"].transform("mean")
    features["vendor_avg_price_ratio"] = (features["unit_price"] / vendor_avg).replace(
        [np.inf, -np.inf], 1.0
    )

    features[FEATURE_COLUMNS] = features[FEATURE_COLUMNS].fillna(features[FEATURE_COLUMNS].median())
    return features