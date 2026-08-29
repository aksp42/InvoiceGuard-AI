"""
Report service.

Builds the validation summary (KPIs) and produces downloadable exports
(CSV, Excel, PDF) from the last processed dataframe.
"""
import io

import pandas as pd

from backend.app.schemas import InvoiceResult, ValidationSummary, ValidationIssue

# In-memory cache of the last processed report (demo-friendly; swap for DB writes in production)
_last_report_df: pd.DataFrame | None = None


def set_last_report(df: pd.DataFrame) -> None:
    global _last_report_df
    _last_report_df = df


def get_last_report() -> pd.DataFrame | None:
    return _last_report_df


def compute_expected_total(row) -> float | None:
    """Row-level expected amount: qty x price (+ GST)."""
    try:
        if pd.isna(row.get("quantity")) or pd.isna(row.get("unit_price")):
            return None
        subtotal = float(row["quantity"]) * float(row["unit_price"])
        return round(subtotal + subtotal * (float(row.get("gst_percent", 0) or 0) / 100), 2)
    except (TypeError, ValueError):
        return None


def build_results(df: pd.DataFrame) -> list[InvoiceResult]:
    results = []
    for _, row in df.iterrows():
        results.append(InvoiceResult(
            invoice_id=str(row["invoice_id"]),
            vendor_name=None if pd.isna(row.get("vendor_name")) else row["vendor_name"],
            total_amount=None if pd.isna(row.get("total_amount")) else float(row["total_amount"]),
            expected_total=compute_expected_total(row),
            status=row["status"],
            risk_score=float(row["risk_score"]),
            issues=[ValidationIssue(**i) for i in row["issues"]],
        ))
    return results


def build_summary(df: pd.DataFrame) -> ValidationSummary:
    return ValidationSummary(
        total_invoices=len(df),
        valid_count=int((df["status"] == "Valid").sum()),
        high_risk_count=int((df["status"] == "High Risk").sum()),
        duplicate_count=int((df["status"] == "Duplicate").sum()),
        total_flagged_amount=float(df.loc[df["status"] != "Valid", "total_amount"].fillna(0).sum()),
        results=build_results(df),
    )


def report_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Flat export view of the report (one column set, CSV/Excel friendly)."""
    export_df = df[["invoice_id", "vendor_name", "total_amount", "status", "risk_score"]].copy()
    export_df["issues_summary"] = df["issues"].map(
        lambda items: "; ".join(i["code"] for i in items) if items else ""
    )
    return export_df


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    report_dataframe(df).to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    report_dataframe(df).to_excel(out, index=False, engine="openpyxl")
    return out.getvalue()