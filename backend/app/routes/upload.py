"""Invoice upload pipeline endpoints (Phase 3 + Phase 3.1 security).

POST /api/upload/single   — exactly one invoice per file
POST /api/upload/bulk     — many invoices per file
GET  /api/upload/history  — recent upload batches
GET  /api/upload/{batch_id}  — single batch + invoice summary

Phase 3.1 upload security:
  - extension + MIME verification against a per-extension allow list
  - 20 MB size cap enforced WHILE streaming (huge files never load fully)
  - file-name sanitisation (no directory components / control characters)
  - xlsx magic-byte (zip header) sniffing before parsing
  - guaranteed file-handle cleanup (try/finally on the spooled file)
  - pre-flight rejections happen BEFORE any batch row is created, so invalid
    payloads never touch the database; each rejection is still audit-logged
    as an "Upload Failed" event with batch_id=none.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db, read_guard
from backend.app.models import Invoice, UploadBatch
from backend.app.schemas import (
    BatchDetail,
    BatchInvoice,
    UploadHistoryItem,
    UploadSummary,
)
from backend.app.services import upload_service

router = APIRouter(prefix="/api/upload", tags=["upload"])

_EXTENSIONS = {".csv", ".xlsx"}
_CHUNK_SIZE = 1024 * 1024

# Content types accepted per extension. application/octet-stream is tolerated
# because several proxies / native clients send it for any binary payload.
_CONTENT_TYPES = {
    ".csv": {
        "text/csv",
        "application/csv",
        "text/plain",
        "application/vnd.ms-excel",
        "application/octet-stream",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/vnd.ms-excel",
        "application/octet-stream",
    },
}


def _reject_upload(status_code: int, detail: str):
    """Audit-log a pre-flight rejection and raise an HTTP error (no batch row)."""
    upload_service.log_upload_event(None, upload_service.EVENT_UPLOAD_FAILED, detail)
    raise HTTPException(status_code=status_code, detail=detail)


def _read_and_validate(file: UploadFile) -> tuple[str, bytes]:
    """Validate + read an upload; returns (sanitised_name, content).

    Enforces, in order: allowed extension, allowed MIME type, the size cap
    (streamed in 1 MB chunks), non-empty payload and, for .xlsx, the zip magic
    bytes. The spooled file handle is always closed, even on rejection.
    """
    name = upload_service.sanitize_filename(file.filename or "")
    ext = Path(name).suffix.lower()
    if ext not in _EXTENSIONS:
        _reject_upload(
            400,
            f"Unsupported file type '{ext or '<no extension>'}' for '{name}'. Use .csv or .xlsx.",
        )

    content_type = (file.content_type or "").strip().lower()
    if content_type and content_type not in _CONTENT_TYPES[ext]:
        _reject_upload(
            400,
            f"File content type '{content_type}' is not allowed for {ext} uploads.",
        )

    limit = settings.max_upload_size_bytes
    chunks = []
    total = 0
    try:
        while chunk := file.file.read(_CHUNK_SIZE):
            total += len(chunk)
            if total > limit:
                _reject_upload(
                    413,
                    f"File exceeds the {settings.max_upload_size_mb} MB upload limit.",
                )
            chunks.append(chunk)
    finally:
        file.file.close()

    if total == 0:
        _reject_upload(400, "The uploaded file is empty.")

    content = b"".join(chunks)
    if ext == ".xlsx" and content[:2] != b"PK":
        _reject_upload(
            400,
            "Corrupted or invalid Excel file: payload does not look like a .xlsx (Open XML) document.",
        )
    return name, content


def _run_upload(file: UploadFile, db: Session, *, single: bool) -> dict:
    name, content = _read_and_validate(file)
    try:
        return upload_service.process_upload(
            db,
            file_name=name,
            file_bytes=content,
            single=single,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except upload_service.UploadPersistError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/single", response_model=UploadSummary)
def upload_single(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return _run_upload(file, db, single=True)


@router.post("/bulk", response_model=UploadSummary)
def upload_bulk(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return _run_upload(file, db, single=False)


@router.get("/history", response_model=list[UploadHistoryItem])
def upload_history(db: Session = Depends(get_db)):
    batches = read_guard(
        lambda: db.query(UploadBatch).order_by(UploadBatch.batch_id.desc()).limit(50).all()
    )
    return [
        UploadHistoryItem(
            batch_id=b.batch_id,
            file_name=b.file_name,
            uploaded_by=b.uploaded_by,
            uploaded_at=b.uploaded_at.isoformat() if b.uploaded_at else None,
            total_invoices=b.total_invoices,
            processed_invoices=b.processed_invoices,
            failed_invoices=b.failed_invoices,
            status=b.status,
        )
        for b in batches
    ]


@router.get("/{batch_id}", response_model=BatchDetail)
def upload_detail(batch_id: int, db: Session = Depends(get_db)):
    try:
        batch = db.query(UploadBatch).filter_by(batch_id=batch_id).first()
        invoices = (
            db.query(Invoice)
            .filter_by(batch_id=batch_id)
            .order_by(Invoice.invoice_id)
            .all()
        )
    except Exception:  # pragma: no cover - infra dependent
        # Database unavailable → return an empty, well-formed batch detail
        # instead of a 500 so the UI degrades gracefully.
        return BatchDetail(
            batch_id=batch_id,
            file_name="(unavailable)",
            uploaded_by="-",
            uploaded_at=None,
            total_invoices=0,
            processed_invoices=0,
            failed_invoices=0,
            status="Processing",
            invoices=[],
        )
    if batch is None:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found.")
    return BatchDetail(
        batch_id=batch.batch_id,
        file_name=batch.file_name,
        uploaded_by=batch.uploaded_by,
        uploaded_at=batch.uploaded_at.isoformat() if batch.uploaded_at else None,
        total_invoices=batch.total_invoices,
        processed_invoices=batch.processed_invoices,
        failed_invoices=batch.failed_invoices,
        status=batch.status,
        invoices=[
            BatchInvoice(
                invoice_number=i.invoice_number,
                invoice_date=i.invoice_date.isoformat() if i.invoice_date else None,
                vendor_name=i.vendor.vendor_name if i.vendor else None,
                subtotal=i.subtotal,
                tax_amount=i.tax_amount,
                total_amount=i.total_amount,
                status=i.status,
            )
            for i in invoices
        ],
    )