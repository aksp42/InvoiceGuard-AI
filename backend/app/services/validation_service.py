"""Rule-based validation orchestration + persistence (Phase 4).

After an upload completes this service, for one upload batch:

  Upload Completed
      -> load invoices of the batch (+ line items)
      -> run the rule-based validator (validator.assess)
      -> persist each finding into validation_results
      -> update invoices.risk_score and invoices.status
      -> return a batch validation summary

Every run emits audit events through the shared audit logger
(backend/logs/upload_audit.log):
  Validation Started, Validation Completed, Critical Issue Found,
  Batch Validation Completed (+ Upload Failed on a database error).

No duplicate detection, price-anomaly detection, OCR or machine learning is
used in this phase — see future phases.
"""
import logging
import time

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from backend.app.logging_config import get_audit_logger
from backend.app.models import Invoice, UploadBatch, ValidationResult
from backend.app.services import validator
from backend.app.services.rules import CRITICAL

logger = logging.getLogger("invoice")
audit = get_audit_logger()


class BatchNotFoundError(RuntimeError):
    """Raised when the requested upload batch does not exist (HTTP 404)."""


class ValidationError(RuntimeError):
    """Raised when writing validation results / invoice updates fails (HTTP 500)."""


def _audit(batch_id, event: str, details: str = "") -> None:
    audit.info(
        "%s | batch_id=%s | %s",
        event,
        batch_id if batch_id is not None else "none",
        details,
    )


def _get_batch(db, batch_id: int) -> UploadBatch:
    batch = db.query(UploadBatch).filter_by(batch_id=batch_id).first()
    if batch is None:
        raise BatchNotFoundError(f"Batch {batch_id} not found.")
    return batch


def _load_invoices(db, batch_id: int):
    """Load the batch's stored invoices with line items + vendor (no N+1)."""
    return (
        db.query(Invoice)
        .filter_by(batch_id=batch_id)
        .options(joinedload(Invoice.items), joinedload(Invoice.vendor))
        .order_by(Invoice.invoice_id)
        .all()
    )


def _validate_and_persist_invoice(db, invoice, *, today) -> dict:
    """Run the rules for one invoice, persist results + status, return outcome.

    Returns {"invoice_id", "status", "risk_score", "issue_count", "has_critical"}.
    Rows stay un-committed — the caller owns the surrounding transaction.
    """
    outcome = validator.assess(invoice, invoice.items or [], today=today)

    for issue in outcome["issues"]:
        db.add(
            ValidationResult(
                invoice_id=invoice.invoice_id,
                validation_type=issue.validation_type,
                severity=issue.severity,
                message=issue.message,
            )
        )

    invoice.risk_score = outcome["risk_score"]
    invoice.status = outcome["status"]

    return {
        "invoice_id": invoice.invoice_id,
        "status": outcome["status"],
        "risk_score": outcome["risk_score"],
        "issue_count": len(outcome["issues"]),
        "has_critical": outcome["has_critical"],
    }


def validate_batch(db, batch_id: int, *, today=None) -> dict:
    """Validate every stored invoice of a batch; persist + return the summary.

    One database transaction for the whole batch: all validation_results rows
    plus the invoice status/risk updates commit together, or roll back entirely.
    Re-running appends to the historical validation_results trail (it is an
    audit table) and always refreshes the current status / risk score.
    """
    started = time.perf_counter()
    batch = _get_batch(db, batch_id)
    _audit(batch_id, "Validation Started", f"file={batch.file_name}")

    invoices = _load_invoices(db, batch_id)
    counts = {"valid": 0, "needs_review": 0, "high_risk": 0, "critical": 0}

    # Map the invoice status to the summary counter key.
    _STATUS_KEY = {
        "Valid": "valid",
        "Needs Review": "needs_review",
        "High Risk": "high_risk",
        "Critical": "critical",
    }

    try:
        for invoice in invoices:
            outcome = _validate_and_persist_invoice(db, invoice, today=today)
            counts[_STATUS_KEY[outcome["status"]]] += 1
            if outcome["has_critical"]:
                _audit(
                    batch_id,
                    "Critical Issue Found",
                    f"invoice_id={outcome['invoice_id']} "
                    f"status={outcome['status']} risk_score={outcome['risk_score']}",
                )
            _audit(
                batch_id,
                "Validation Completed",
                f"invoice_id={outcome['invoice_id']} status={outcome['status']} "
                f"risk_score={outcome['risk_score']} issues={outcome['issue_count']}",
            )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        _audit(batch_id, "Upload Failed", f"phase=validation error={exc}")
        raise ValidationError(f"Database error while validating batch {batch_id}: {exc}") from exc

    elapsed = time.perf_counter() - started
    summary = {
        "batch_id": batch_id,
        "total_invoices": len(invoices),
        "valid": counts.get("valid", 0),
        "needs_review": counts.get("needs_review", 0),
        "high_risk": counts.get("high_risk", 0),
        "critical": counts.get("critical", 0),
        "validation_time": f"{elapsed:.1f}s",
    }
    _audit(batch_id, "Batch Validation Completed", str(summary))
    logger.info("Validated batch %s: %s", batch_id, summary)
    return summary