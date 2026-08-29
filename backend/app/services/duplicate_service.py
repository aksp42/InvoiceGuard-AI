"""Duplicate detection orchestration + persistence (Phase 5).

After validation completes, `scan_duplicates` compares every invoice of an
upload batch against every other invoice of the same company (both older
batches and siblings inside the current one) using the deterministic rules in
duplicate_rules.py. Every finding is written into validation_results (both
sides of the match), and the risk score of every affected invoice is
refreshed:

    risk = rule_based_risk + duplicate_penalties   (capped at 100)

Duplicate penalties are derived from the DISTINCT (validation_type, pair)
combinations. Pair keys are stable across re-runs, so re-scanning the same
batch never double-charges the penalty (the validation_results trail does
grow, as it is an append-only audit table).

Audit events (existing invoice.audit logger):
  Duplicate Detection Started / Exact Duplicate Found / Near Duplicate Found /
  Duplicate Match Found / Batch Duplicate Scan Completed (+ Upload Failed).

No OCR, no LLM, no ML — only deterministic rules + lightweight RapidFuzz
fuzzy matching where the phase brief asks for it (Level 3).
"""
import logging
import re
import time

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from backend.app.logging_config import get_audit_logger
from backend.app.models import Invoice, UploadBatch, ValidationResult
from backend.app.services import validator
from backend.app.services.duplicate_matcher import DATE_WINDOW_DAYS
from backend.app.services.duplicate_rules import (
    detect,
    DUPLICATE_CODE_TO_CATEGORY,
    DUPLICATE_CODES,
    LEVEL_PENALTY,
)
from backend.app.services.validation_service import BatchNotFoundError

logger = logging.getLogger("invoice")
audit = get_audit_logger()

# Each detectable rule maps to a summary counter bucket.
_EXTRACT_MATCH_ID = re.compile(r"match_id=(\d+)")
_EXTRACT_SIMILARITY = re.compile(r"similarity=([\d.]+)")

_AUDIT_EVENT = {
    "DUPLICATE_EXACT": "Exact Duplicate Found",
    "DUPLICATE_NEAR": "Near Duplicate Found",
    # vendor / date / item matches share the generic event below.
}

_SEVERITY_RANK = {"CRITICAL": 0, "ERROR": 1, "WARNING": 2, "INFO": 3}


class DuplicateScanError(RuntimeError):
    """Raised when persisting duplicate results fails (HTTP 500)."""


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


def _load_batch_invoices(db, batch_id: int):
    return (
        db.query(Invoice)
        .filter_by(batch_id=batch_id)
        .options(joinedload(Invoice.items), joinedload(Invoice.vendor))
        .order_by(Invoice.invoice_id)
        .all()
    )


def _load_company_invoices(db, company_ids: set[int]):
    """All invoices of the tenant(s) owning the batch, pre-loaded with items/vendor."""
    query = db.query(Invoice).options(
        joinedload(Invoice.items), joinedload(Invoice.vendor)
    )
    if company_ids:
        query = query.filter(Invoice.company_id.in_(company_ids))
    return query.order_by(Invoice.invoice_id).all()


def _pair_key(validation_type: str, invoice_id: int, other_id: int) -> tuple:
    """Stable key for one duplicated pair — identical no matter which side."""
    return (validation_type, frozenset((invoice_id, other_id)))


def _existing_pair_keys(db) -> dict[int, set]:
    """Pairs already on record (from earlier scans), keyed per invoice id.

    Parsed back from the structured tokens embedded in each stored message
    (`match_id=...`), so penalty computation never double-charges re-runs.
    """
    rows = (
        db.query(ValidationResult)
        .filter(ValidationResult.validation_type.in_(DUPLICATE_CODES))
        .all()
    )
    logged: dict[int, set] = {}
    for row in rows:
        found = _EXTRACT_MATCH_ID.search(row.message or "")
        if not found:
            continue
        other_id = int(found.group(1))
        if other_id == row.invoice_id:
            continue
        logged.setdefault(row.invoice_id, set()).add(
            _pair_key(row.validation_type, row.invoice_id, other_id)
        )
    return logged


def _describe(match, self_invoice, other_invoice) -> str:
    other = f"invoice #{other_invoice.invoice_id} ({other_invoice.invoice_number})"
    vendor = (
        self_invoice.vendor.vendor_name
        if self_invoice.vendor is not None
        else "unknown"
    )
    amount = self_invoice.total_amount
    if match.validation_type == "DUPLICATE_EXACT":
        return (
            f"Exact duplicate: {self_invoice.invoice_number!r} already exists as {other}."
        )
    if match.validation_type == "DUPLICATE_VENDOR":
        return (
            f"Vendor duplicate: same vendor {vendor} and amount {amount} and "
            f"invoice date as {other}."
        )
    if match.validation_type == "DUPLICATE_NEAR":
        sim = int(match.similarity or 0)
        return (
            f"Near duplicate: invoice number {sim}% similar to {other} "
            f"(same vendor {vendor}, amount differs by <= Rs.1)."
        )
    if match.validation_type == "DUPLICATE_DATE":
        return (
            f"Suspicious amount+date match: same vendor {vendor} and amount "
            f"{amount} as {other} within {DATE_WINDOW_DAYS} days."
        )
    if match.validation_type == "DUPLICATE_ITEM":
        return (
            f"Suspicious item-level duplicate: identical line items as {other}."
        )
    return f"Duplicate match with {other}."


def _stored_message(match, self_invoice, other_invoice) -> str:
    """Human-readable message + machine-parseable tokens for the duplicate table."""
    message = _describe(match, self_invoice, other_invoice)
    message += (
        f" | match_id={other_invoice.invoice_id}"
        f" | match_number={other_invoice.invoice_number}"
    )
    if match.similarity is not None:
        message += f" | similarity={match.similarity}"
    return message[:500]


def _apply_risk(db, invoice, pair_keys: set) -> None:
    """Refresh an invoice's risk from rule-based risk + duplicate penalties.

    Rule-based risk is recomputed deterministically (validator.assess), so the
    result is stable no matter how many times the batch is re-scanned.
    """
    rule_result = validator.assess(invoice, invoice.items or [])
    penalty = sum(
        LEVEL_PENALTY.get(validation_type, 0) for validation_type, _ in pair_keys
    )
    new_score = round(min(rule_result["risk_score"] + penalty, 100.0), 2)
    invoice.risk_score = new_score
    invoice.status = validator.status_for_score(new_score)


def _summary(batch_id: int, counts: dict) -> dict:
    return {
        "batch_id": batch_id,
        "exact_duplicates": counts["exact"],
        "vendor_duplicates": counts["vendor"],
        "near_duplicates": counts["near"],
        "suspicious_duplicates": counts["date"] + counts["item"],
    }


def scan_duplicates(db, batch_id: int, *, today=None) -> dict:
    """Scan one upload batch for duplicates against the whole tenant database.

    One transaction for the entire scan: findings + risk/status updates commit
    together or roll back together.
    """
    started = time.perf_counter()
    batch = _get_batch(db, batch_id)
    _audit(batch_id, "Duplicate Detection Started", f"file={batch.file_name}")

    batch_invoices = _load_batch_invoices(db, batch_id)
    counts = {"exact": 0, "vendor": 0, "near": 0, "date": 0, "item": 0}

    if not batch_invoices:
        summary = _summary(batch_id, counts)
        _audit(batch_id, "Batch Duplicate Scan Completed", str(summary))
        return summary

    company_ids = {
        invoice.company_id for invoice in batch_invoices if invoice.company_id is not None
    }
    candidates = _load_company_invoices(db, company_ids)
    batch_ids = {invoice.invoice_id for invoice in batch_invoices}

    logged = _existing_pair_keys(db)
    scanned: dict[int, set] = {}

    try:
        for current in batch_invoices:
            for other in candidates:
                if other.invoice_id == current.invoice_id:
                    continue
                # A pair with BOTH sides in this batch is evaluated once —
                # when the lower invoice id is the anchor.
                if (
                    other.invoice_id in batch_ids
                    and other.invoice_id < current.invoice_id
                ):
                    continue

                match = detect(current, other)
                if match is None:
                    continue

                counts[DUPLICATE_CODE_TO_CATEGORY[match.validation_type]] += 1

                details = (
                    f"invoice_id={current.invoice_id} <-> invoice_id={other.invoice_id}"
                )
                if match.similarity is not None:
                    details += f" similarity={match.similarity}"
                event = _AUDIT_EVENT.get(match.validation_type, "Duplicate Match Found")
                _audit(batch_id, event, details)

                # Persist the finding on BOTH sides of the match.
                db.add(
                    ValidationResult(
                        invoice_id=current.invoice_id,
                        validation_type=match.validation_type,
                        severity=match.severity,
                        message=_stored_message(match, current, other),
                        confidence_score=match.confidence,
                    )
                )
                db.add(
                    ValidationResult(
                        invoice_id=other.invoice_id,
                        validation_type=match.validation_type,
                        severity=match.severity,
                        message=_stored_message(match, other, current),
                        confidence_score=match.confidence,
                    )
                )

                scanned.setdefault(current.invoice_id, set()).add(
                    _pair_key(match.validation_type, current.invoice_id, other.invoice_id)
                )
                scanned.setdefault(other.invoice_id, set()).add(
                    _pair_key(match.validation_type, current.invoice_id, other.invoice_id)
                )

        for invoice in candidates:
            if invoice.invoice_id not in scanned:
                continue
            _apply_risk(db, invoice, logged.get(invoice.invoice_id, set()) | scanned[invoice.invoice_id])

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        _audit(batch_id, "Upload Failed", f"phase=duplicates error={exc}")
        raise DuplicateScanError(f"Database error while scanning batch {batch_id}: {exc}") from exc

    elapsed = time.perf_counter() - started
    summary = _summary(batch_id, counts)
    _audit(batch_id, "Batch Duplicate Scan Completed", str(summary))
    logger.info(
        "Scanned batch %s for duplicates in %.1fs: %s", batch_id, elapsed, summary
    )
    return summary


def list_duplicate_pairs(db) -> list[dict]:
    """Denormalised, deduplicated pair rows for the Duplicates page.

    One row per distinct (validation_type, pair) found in validation_results —
    so re-scans never duplicate rows. Includes both invoice ids/numbers,
    vendor, amounts, dates, severity, confidence and the fuzzy similarity
    (Level 3) extracted from the stored message tokens.
    """
    rows = (
        db.query(ValidationResult)
        .filter(ValidationResult.validation_type.in_(DUPLICATE_CODES))
        .order_by(ValidationResult.validation_id)
        .all()
    )
    if not rows:
        return []

    invoice_ids = {row.invoice_id for row in rows}
    for row in rows:
        found = _EXTRACT_MATCH_ID.search(row.message or "")
        if found:
            invoice_ids.add(int(found.group(1)))
    if not invoice_ids:
        return []

    invoices = {
        invoice.invoice_id: invoice
        for invoice in db.query(Invoice)
        .filter(Invoice.invoice_id.in_(invoice_ids))
        .options(joinedload(Invoice.vendor))
        .all()
    }

    pairs: dict[tuple, dict] = {}
    for row in rows:
        found = _EXTRACT_MATCH_ID.search(row.message or "")
        if not found:
            continue
        other_id = int(found.group(1))
        key = _pair_key(row.validation_type, row.invoice_id, other_id)
        if key in pairs:
            continue

        id_a, id_b = min(row.invoice_id, other_id), max(row.invoice_id, other_id)
        inv_a, inv_b = invoices.get(id_a), invoices.get(id_b)
        sim_found = _EXTRACT_SIMILARITY.search(row.message or "")
        similarity = float(sim_found.group(1)) if sim_found else None

        pairs[key] = {
            "invoice_a_id": id_a,
            "invoice_a_number": inv_a.invoice_number if inv_a else None,
            "invoice_b_id": id_b,
            "invoice_b_number": inv_b.invoice_number if inv_b else None,
            "vendor_name": (
                inv_a.vendor.vendor_name
                if inv_a and inv_a.vendor is not None
                else (inv_b.vendor.vendor_name if inv_b and inv_b.vendor is not None else None)
            ),
            "amount_a": inv_a.total_amount if inv_a else None,
            "amount_b": inv_b.total_amount if inv_b else None,
            "invoice_date_a": inv_a.invoice_date.isoformat() if inv_a and inv_a.invoice_date else None,
            "invoice_date_b": inv_b.invoice_date.isoformat() if inv_b and inv_b.invoice_date else None,
            "matched_ids": [id_a, id_b],
            "validation_type": row.validation_type,
            "severity": row.severity,
            "confidence_score": row.confidence_score,
            "similarity": similarity,
        }

    ordered = sorted(
        pairs.values(),
        key=lambda p: (_SEVERITY_RANK.get(p["severity"], 9), p["invoice_a_id"]),
    )
    return ordered