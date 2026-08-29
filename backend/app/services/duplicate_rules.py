"""Duplicate detection rules (Phase 5).

Each level is a pure, deterministic decision rule taking two invoices:

    rule(invoice_a, invoice_b) -> DuplicateMatch | None

Levels (evaluated in priority order by `detect`; the FIRST match on a pair
wins so a pair is never double-counted at several levels):

    L1 DUPLICATE_EXACT   same company + same invoice_number        CRITICAL / 100 / +50
    L2 DUPLICATE_VENDOR  same vendor + amount + invoice date       CRITICAL /  98 / +40
    L3 DUPLICATE_NEAR    same vendor + number sim >= 90% + diff<=Rs.1  ERROR / 95 / +30
    L4 DUPLICATE_DATE    same vendor + amount + dates within 3 days     WARNING / 85 / +15
    L5 DUPLICATE_ITEM    identical line items (name/qty/unit price)      ERROR / 92 / +25

Rules only DECIDE. Persistence, risk updates and audit live in
duplicate_service.py.
"""
from dataclasses import dataclass

from backend.app.services.duplicate_matcher import (
    amounts_equal,
    amounts_near,
    dates_close,
    dates_equal,
    invoice_number_similarity,
    items_identical,
    NUMBER_SIMILARITY_THRESHOLD,
)

# validation_type codes (subset of schema.sql chk_validation_type)
DUPLICATE_EXACT = "DUPLICATE_EXACT"
DUPLICATE_VENDOR = "DUPLICATE_VENDOR"
DUPLICATE_NEAR = "DUPLICATE_NEAR"
DUPLICATE_DATE = "DUPLICATE_DATE"
DUPLICATE_ITEM = "DUPLICATE_ITEM"

DUPLICATE_CODES = (
    DUPLICATE_EXACT,
    DUPLICATE_VENDOR,
    DUPLICATE_NEAR,
    DUPLICATE_DATE,
    DUPLICATE_ITEM,
)

# Per-level metadata (severity / confidence / extra risk), per the phase brief.
LEVEL_SEVERITY = {
    DUPLICATE_EXACT: "CRITICAL",
    DUPLICATE_VENDOR: "CRITICAL",
    DUPLICATE_NEAR: "ERROR",
    DUPLICATE_DATE: "WARNING",
    DUPLICATE_ITEM: "ERROR",
}

LEVEL_CONFIDENCE = {
    DUPLICATE_EXACT: 100.0,
    DUPLICATE_VENDOR: 98.0,
    DUPLICATE_NEAR: 95.0,
    DUPLICATE_DATE: 85.0,
    DUPLICATE_ITEM: 92.0,
}

LEVEL_PENALTY = {
    DUPLICATE_EXACT: 50,
    DUPLICATE_VENDOR: 40,
    DUPLICATE_NEAR: 30,
    DUPLICATE_DATE: 15,
    DUPLICATE_ITEM: 25,
}

# Maps a detected type back to the scan summary counter bucket.
DUPLICATE_CODE_TO_CATEGORY = {
    DUPLICATE_EXACT: "exact",
    DUPLICATE_VENDOR: "vendor",
    DUPLICATE_NEAR: "near",
    DUPLICATE_DATE: "date",
    DUPLICATE_ITEM: "item",
}


@dataclass
class DuplicateMatch:
    """One detected duplicate finding between two invoices."""

    validation_type: str
    severity: str
    confidence: float
    penalty: int
    similarity: float | None = None
    note: str = ""


def _same_company(a, b) -> bool:
    """Duplicates only exist when both invoices belong to the same tenant."""
    if a.company_id is not None and b.company_id is not None:
        return a.company_id == b.company_id
    return True


def _same_vendor(a, b) -> bool:
    """Vendor-scoped duplicate matches require the SAME vendor AND tenant.

    vendor_id is globally unique in this schema, but the guard is kept so the
    rule stays correct even if vendors are ever tenant-agnostic.
    """
    return (
        getattr(a, "vendor_id", None) is not None
        and a.vendor_id == b.vendor_id
        and _same_company(a, b)
    )


def _same_number(a, b) -> bool:
    left = (a.invoice_number or "").strip().lower()
    right = (b.invoice_number or "").strip().lower()
    return bool(left) and left == right


# ---------------------------------------------------------------------------
# Level 1 — Exact duplicate: same company + same invoice_number
# ---------------------------------------------------------------------------
def exact_duplicate(a, b) -> DuplicateMatch | None:
    if _same_number(a, b) and _same_company(a, b):
        return DuplicateMatch(
            DUPLICATE_EXACT,
            "CRITICAL",
            100.0,
            50,
            note=f"identical invoice number {a.invoice_number!r}",
        )
    return None


# ---------------------------------------------------------------------------
# Level 2 — Vendor duplicate: same vendor + amount + invoice date
# ---------------------------------------------------------------------------
def vendor_duplicate(a, b) -> DuplicateMatch | None:
    if (
        _same_vendor(a, b)
        and amounts_equal(a.total_amount, b.total_amount)
        and dates_equal(a.invoice_date, b.invoice_date)
    ):
        return DuplicateMatch(
            DUPLICATE_VENDOR,
            "CRITICAL",
            98.0,
            40,
            note="same vendor, amount and invoice date",
        )
    return None


# ---------------------------------------------------------------------------
# Level 3 — Near duplicate: same vendor + number similarity >= 90% + diff <= Rs.1
# ---------------------------------------------------------------------------
def near_duplicate(a, b) -> DuplicateMatch | None:
    if not _same_vendor(a, b) or not amounts_near(a.total_amount, b.total_amount):
        return None
    similarity = invoice_number_similarity(a.invoice_number, b.invoice_number)
    if similarity >= NUMBER_SIMILARITY_THRESHOLD:
        return DuplicateMatch(
            DUPLICATE_NEAR,
            "ERROR",
            95.0,
            30,
            similarity=similarity,
            note=f"invoice numbers {int(similarity)}% similar",
        )
    return None


# ---------------------------------------------------------------------------
# Level 4 — Amount & date match: same vendor + amount + dates within 3 days
# ---------------------------------------------------------------------------
def amount_date_match(a, b) -> DuplicateMatch | None:
    if (
        _same_vendor(a, b)
        and amounts_equal(a.total_amount, b.total_amount)
        and dates_close(a.invoice_date, b.invoice_date)
    ):
        return DuplicateMatch(
            DUPLICATE_DATE,
            "WARNING",
            85.0,
            15,
            note="same vendor and amount within 3 days",
        )
    return None


# ---------------------------------------------------------------------------
# Level 5 — Item-level duplicate: identical line items (name/qty/unit price)
# ---------------------------------------------------------------------------
def item_duplicate(a, b) -> DuplicateMatch | None:
    if _same_company(a, b) and items_identical(a.items, b.items):
        return DuplicateMatch(
            DUPLICATE_ITEM,
            "ERROR",
            92.0,
            25,
            note="identical line items",
        )
    return None


# Rules in priority order — `detect` returns the FIRST (highest-level) match.
RULE_ORDER = (
    exact_duplicate,
    vendor_duplicate,
    near_duplicate,
    amount_date_match,
    item_duplicate,
)


def detect(a, b) -> DuplicateMatch | None:
    """Return the highest-priority duplicate level for the pair (or None)."""
    for rule in RULE_ORDER:
        match = rule(a, b)
        if match is not None:
            return match
    return None