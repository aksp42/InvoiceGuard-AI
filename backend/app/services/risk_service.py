"""
Risk scoring service.

Blends the rule-based issues with the Isolation Forest ML risk score into a
single 0-100 risk score and a final status:
  - Duplicate        -> always forced (unambiguous financial error)
  - High Risk        -> total mismatch, or combined score >= 50, or ML flag
  - Needs Review     -> any other rule issue
  - Valid            -> no issues
"""
import pandas as pd

from backend.app.config import ML_ENABLED
from ml_engine.predict import score_invoices


def final_status_and_score(row_codes: set[str], rule_score: float, ml_risk: float, ml_flag: bool):
    """Pure function: take the decoded rule codes + ML outputs, return (status, score)."""

    combined_score = round(min(100.0, max(rule_score, ml_risk * 0.6 + rule_score * 0.4)), 1)

    if "DUPLICATE_INVOICE" in row_codes:
        return "Duplicate", 100.0
    if "TOTAL_MISMATCH" in row_codes or combined_score >= 50 or ml_flag:
        return "High Risk", round(max(combined_score, 60.0), 1)
    if row_codes:
        return "Needs Review", combined_score
    return "Valid", combined_score


def rule_component(codes: set[str]) -> float:
    """Weighted contribution of rule issues (mirrors original main.py scoring)."""
    score = 0.0
    score += 40 if "TOTAL_MISMATCH" in codes else 0
    score += 15 if "MISSING_FIELD" in codes else 0
    score += 15 if "PRICE_OUTLIER" in codes else 0
    score += 10 if ("FUTURE_DATE" in codes or "INVALID_DATE" in codes) else 0
    return score


def score_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Adds status + risk_score columns to a dataframe that already has an 'issues' column."""
    if ML_ENABLED:
        df = score_invoices(df)  # adds ml_risk_score + ml_flag
    else:
        df = df.copy()
        df["ml_risk_score"] = 0.0
        df["ml_flag"] = False

    statuses, scores = [], []
    for _, row in df.iterrows():
        codes = {i["code"] for i in row["issues"]}
        rule_score = rule_component(codes)
        status, score = final_status_and_score(codes, rule_score, row["ml_risk_score"], row["ml_flag"])
        statuses.append(status)
        scores.append(score)

    out = df.copy()
    out["status"] = statuses
    out["risk_score"] = scores
    return out