"""Report download endpoints (CSV / Excel / PDF)."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.services.report_service import get_last_report, to_csv_bytes, to_excel_bytes
from backend.app.utils.pdf_export import to_pdf_bytes

router = APIRouter(prefix="/api/report", tags=["reports"])

_HEADERS = {
    "csv": ("attachment; filename=invoice_validation_report.csv", "text/csv"),
    "xlsx": ("attachment; filename=invoice_validation_report.xlsx",
             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "pdf": ("attachment; filename=invoice_validation_report.pdf", "application/pdf"),
}


def _require_report():
    df = get_last_report()
    if df is None:
        raise HTTPException(status_code=404, detail="No report generated yet — call /api/upload first")
    return df


@router.get("/csv")
def download_report_csv():
    df = _require_report()
    return StreamingResponse(
        iter([to_csv_bytes(df)]),
        media_type=_HEADERS["csv"][1],
        headers={"Content-Disposition": _HEADERS["csv"][0]},
    )


@router.get("/excel")
def download_report_excel():
    df = _require_report()
    return StreamingResponse(
        iter([to_excel_bytes(df)]),
        media_type=_HEADERS["xlsx"][1],
        headers={"Content-Disposition": _HEADERS["xlsx"][0]},
    )


@router.get("/pdf")
def download_report_pdf():
    df = _require_report()
    export_df = df[["invoice_id", "vendor_name", "total_amount", "status", "risk_score"]].copy()
    rows = [tuple(export_df.columns)] + [tuple(r) for r in export_df.itertuples(index=False)]
    return StreamingResponse(
        iter([to_pdf_bytes(rows)]),
        media_type=_HEADERS["pdf"][1],
        headers={"Content-Disposition": _HEADERS["pdf"][0]},
    )