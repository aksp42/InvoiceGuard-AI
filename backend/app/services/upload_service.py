"""Upload pipeline orchestration (Phase 3 + Phase 3.1 hardening).

Single responsibilities, kept in small functions:
  - create the upload batch (status Processing)
  - parse the file through parser_service
  - group standardised rows into invoices (by invoice_number)
  - compute line totals / subtotal / tax / total from qty, price, gst%
  - persist invoices + items, updating processed/failed counts
  - mark the batch Completed (or Failed on any error)

Phase 3.1 production hardening:
  - transaction safety: every upload persists in ONE database transaction.
    Invoice/vendor saves run inside a nested savepoint; a fatal database error
    rolls the savepoint back (no partial invoices), then the batch row —
    created before the savepoint — is committed as Failed in the same outer
    transaction.
  - audit trail: Upload Started / Parsing Started / Parsing Completed /
    Database Save Started / Database Save Completed / Upload Failed /
    Upload Completed events are appended to backend/logs/upload_audit.log
    with timestamp, batch_id, event and details.

No invoice validation / duplicate / GST / anomaly logic lives here — those
belong to later phases.
"""
import logging
import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from backend.app.logging_config import get_audit_logger
from backend.app.models import Company, Invoice, InvoiceItem, UploadBatch, Vendor
from backend.app.services.parser_service import parse_file

logger = logging.getLogger("invoice")
audit = get_audit_logger()

DEFAULT_COMPANY_ID = 1
DEFAULT_UPLOADED_BY = "admin"

# Upload audit events, in the order they fire for a successful upload.
EVENT_UPLOAD_STARTED = "Upload Started"
EVENT_PARSING_STARTED = "Parsing Started"
EVENT_PARSING_COMPLETED = "Parsing Completed"
EVENT_SAVE_STARTED = "Database Save Started"
EVENT_SAVE_COMPLETED = "Database Save Completed"
EVENT_UPLOAD_FAILED = "Upload Failed"
EVENT_UPLOAD_COMPLETED = "Upload Completed"


class UploadPersistError(RuntimeError):
    """Raised when parsed rows could not be stored in the database."""


def sanitize_filename(raw: str) -> str:
    """Strip directory components and control characters from a file name.

    Prevents path traversal ('..\\hack.csv' -> 'hack.csv') and guarantees the
    value fits the file_name column. Falls back to 'upload' when nothing
    remains.
    """
    name = Path(raw or "").name.strip() or "upload"
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()
    return (name or "upload")[:255]


def log_upload_event(batch_id, event: str, details: str = "") -> None:
    """Append one audit event: timestamp | event | batch_id | details."""
    audit.info(
        "%s | batch_id=%s | %s",
        event,
        batch_id if batch_id is not None else "none",
        details,
    )


def _round2(value) -> float:
    return round(float(value) + 1e-9, 2)


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_date(value):
    """Accept YYYY-MM-DD, DD/MM/YYYY or MM/DD/YYYY; else None."""
    raw = _clean(value)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(value) -> float:
    """Parse a numeric cell; strips commas / percent signs. Raises on empty/garbage."""
    raw = _clean(value).replace(",", "").replace("%", "")
    if not raw:
        raise ValueError("empty numeric value")
    return float(raw)


def create_batch(db, file_name: str, uploaded_by: str = DEFAULT_UPLOADED_BY) -> UploadBatch:
    """Create the upload batch row (status Processing)."""
    batch = UploadBatch(file_name=file_name, uploaded_by=uploaded_by, status="Processing")
    db.add(batch)
    db.flush()
    return batch


def ensure_company(db) -> int:
    """Make sure the default company exists (mirrors the seed data)."""
    company = db.query(Company).filter_by(company_id=DEFAULT_COMPANY_ID).first()
    if company is None:
        company = Company(
            company_id=DEFAULT_COMPANY_ID,
            company_name="Akshu Enterprises Pvt Ltd",
            gst_number="27AACCA9603R1ZM",
            email="accounts@akshuenterprises.com",
        )
        db.add(company)
        db.flush()
    return company.company_id


def group_rows(rows):
    """Group standardised rows by invoice_number.

    Returns (groups: {invoice_number: [rows]}, ungrouped: count of rows that
    had no invoice_number and therefore cannot belong to any invoice).
    """
    groups = {}
    ungrouped = 0
    for row in rows:
        invoice_number = _clean(row.get("invoice_number"))
        if not invoice_number:
            ungrouped += 1
            logger.warning("Row without invoice_number skipped during upload.")
            continue
        groups.setdefault(invoice_number, []).append(row)
    return groups, ungrouped


def _get_or_create_vendor(db, company_id: int, vendor_name: str, cache: dict) -> Vendor:
    vendor = cache.get(vendor_name)
    if vendor is None:
        vendor = (
            db.query(Vendor)
            .filter_by(company_id=company_id, vendor_name=vendor_name)
            .first()
        )
        if vendor is None:
            vendor = Vendor(company_id=company_id, vendor_name=vendor_name)
            db.add(vendor)
            db.flush()
        cache[vendor_name] = vendor
    return vendor


def _build_item(row) -> dict:
    """Compute a line item + its money figures from one standardised row."""
    product_name = _clean(row.get("product_name")) or "General"
    quantity = _parse_float(row.get("quantity"))
    unit_price = _parse_float(row.get("unit_price"))
    raw_gst = _clean(row.get("gst_percent"))
    gst_percent = _parse_float(raw_gst) if raw_gst else 0.0

    subtotal = _round2(quantity * unit_price)
    tax_amount = _round2(subtotal * gst_percent / 100.0)
    return {
        "product_name": product_name,
        "quantity": _round2(quantity),
        "unit_price": _round2(unit_price),
        "tax_percent": _round2(gst_percent),
        "line_total": _round2(subtotal + tax_amount),
        "subtotal": subtotal,
        "tax_amount": tax_amount,
    }


def _persist_invoice(db, batch, company_id: int, invoice_number: str, item_rows, vendor_cache) -> bool:
    """Persist one invoice (all its line items) and return True on success.

    Returns False (invoice counted as failed) when the header is unusable —
    e.g. missing vendor_name or an unparseable invoice_date. Rows whose
    numeric cells are invalid are skipped line-by-line (logged, not fatal).
    """
    first = item_rows[0]
    invoice_date = _parse_date(first.get("invoice_date"))
    vendor_name = _clean(first.get("vendor_name"))
    if not vendor_name or invoice_date is None:
        logger.warning("Invoice %s skipped: missing vendor_name or invalid invoice_date.", invoice_number)
        return False

    vendor = _get_or_create_vendor(db, company_id, vendor_name, vendor_cache)

    subtotal = tax_amount = total_amount = 0.0
    items = []
    for row in item_rows:
        try:
            item = _build_item(row)
        except ValueError as exc:
            logger.warning("Line of invoice %s skipped: %s", invoice_number, exc)
            continue
        subtotal += item["subtotal"]
        tax_amount += item["tax_amount"]
        total_amount += item["line_total"]
        items.append(
            InvoiceItem(
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                tax_percent=item["tax_percent"],
                line_total=item["line_total"],
            )
        )

    invoice = Invoice(
        company_id=company_id,
        vendor_id=vendor.vendor_id,
        invoice_number=invoice_number,
        batch_id=batch.batch_id,
        invoice_date=invoice_date,
        subtotal=_round2(subtotal),
        tax_amount=_round2(tax_amount),
        total_amount=_round2(total_amount),
        status="Pending",
        risk_score=0.0,
    )
    db.add(invoice)
    db.flush()
    for item in items:
        item.invoice_id = invoice.invoice_id
        db.add(item)
    return True


def save_groups(db, batch, company_id: int, groups: dict) -> tuple:
    """Persist all invoice groups; return (processed, failed) counts.

    Never commits or rolls back itself — the caller owns the surrounding
    transaction so the whole upload stays atomic (Phase 3.1).
    """
    vendor_cache = {}
    processed = failed = 0
    for invoice_number, item_rows in groups.items():
        try:
            stored = _persist_invoice(db, batch, company_id, invoice_number, item_rows, vendor_cache)
        except SQLAlchemyError as exc:
            raise UploadPersistError(
                f"Database error while storing invoice '{invoice_number}': {exc}"
            ) from exc
        if stored:
            processed += 1
        else:
            failed += 1
    return processed, failed


def _mark_batch_failed(db, batch) -> None:
    """Commit the batch row as Failed in the current outer transaction.

    Called from failure paths after the savepoint (if one was started) has
    been rolled back. The batch row was flushed before the savepoint, so it is
    still pending and is committed here with status Failed.
    """
    batch.status = "Failed"
    try:
        db.commit()
    except SQLAlchemyError as exc:
        logger.error("Could not persist Failed status for batch %s: %s", batch.batch_id, exc)


def process_upload(db, *, file_name: str, file_bytes: bytes, single: bool = False,
                   uploaded_by: str = DEFAULT_UPLOADED_BY) -> dict:
    """Full pipeline: create batch -> parse -> group -> persist -> summary.

    Parser-level errors mark the batch Failed and are re-raised (the route maps
    them to HTTP 400). Database errors roll back the upload's savepoint — no
    partial invoices are ever committed — then the batch is committed as
    Failed and the error is wrapped in UploadPersistError (HTTP 500).
    """
    file_name = sanitize_filename(file_name)
    batch = create_batch(db, file_name, uploaded_by)
    log_upload_event(
        batch.batch_id,
        EVENT_UPLOAD_STARTED,
        f"file={file_name} bytes={len(file_bytes)} "
        f"mode={'single' if single else 'bulk'}",
    )

    try:
        log_upload_event(batch.batch_id, EVENT_PARSING_STARTED, f"file={file_name}")
        rows = parse_file(file_name, file_bytes)
    except ValueError as exc:
        log_upload_event(batch.batch_id, EVENT_UPLOAD_FAILED, f"phase=parsing error={exc}")
        _mark_batch_failed(db, batch)
        raise
    log_upload_event(batch.batch_id, EVENT_PARSING_COMPLETED, f"rows={len(rows)}")

    groups, ungrouped = group_rows(rows)
    if single and len(groups) > 1:
        log_upload_event(
            batch.batch_id,
            EVENT_UPLOAD_FAILED,
            f"phase=policy file contains {len(groups)} invoices; use bulk upload",
        )
        _mark_batch_failed(db, batch)
        raise ValueError(
            f"Single upload file contains {len(groups)} invoices; use bulk upload instead."
        )

    total = len(groups) + ungrouped
    log_upload_event(
        batch.batch_id,
        EVENT_SAVE_STARTED,
        f"invoice_groups={len(groups)} ungrouped_rows={ungrouped}",
    )

    try:
        # ONE transaction per upload: invoice/vendor work runs in a nested
        # savepoint so any fatal DB error rolls back this whole upload (no
        # partial saves) while the batch row — flushed before the savepoint —
        # survives to be committed as Failed below.
        with db.begin_nested():
            company_id = ensure_company(db)
            processed, failed = save_groups(db, batch, company_id, groups)
    except (SQLAlchemyError, UploadPersistError) as exc:
        log_upload_event(batch.batch_id, EVENT_UPLOAD_FAILED, f"phase=database save error={exc}")
        _mark_batch_failed(db, batch)
        if isinstance(exc, UploadPersistError):
            raise
        raise UploadPersistError(f"Database error while processing upload: {exc}") from exc

    log_upload_event(batch.batch_id, EVENT_SAVE_COMPLETED, f"processed={processed} failed={failed}")

    failed += ungrouped
    batch.total_invoices = total
    batch.processed_invoices = processed
    batch.failed_invoices = failed
    batch.status = "Completed"
    try:
        db.commit()
    except SQLAlchemyError as exc:
        log_upload_event(batch.batch_id, EVENT_UPLOAD_FAILED, f"phase=finalise error={exc}")
        raise UploadPersistError(f"Database error while finalising upload: {exc}") from exc

    summary = {
        "batch_id": batch.batch_id,
        "file_name": batch.file_name,
        "total": total,
        "processed": processed,
        "failed": failed,
        "status": batch.status,
    }
    log_upload_event(batch.batch_id, EVENT_UPLOAD_COMPLETED, str(summary))
    return summary