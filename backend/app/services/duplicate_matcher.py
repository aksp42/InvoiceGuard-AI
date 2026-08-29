"""Similarity + equality helpers for duplicate detection (Phase 5).

Pure, dependency-light functions used by duplicate_rules.py. RapidFuzz is the
preferred fuzzy engine (token_sort_ratio + ratio per the phase brief); the
standard-library difflib fallback keeps the module importable if RapidFuzz is
ever missing.
"""
from difflib import SequenceMatcher

# Tolerance used to consider two amounts "the same" (L2 / L4).
AMOUNT_EQUAL_TOLERANCE = 0.01

# Maximum allowed amount difference for a near duplicate (L3, RS.1).
NEAR_AMOUNT_TOLERANCE = 1.00

# Invoice-number similarity threshold for a near duplicate (L3, >= 90%).
NUMBER_SIMILARITY_THRESHOLD = 90.0

# Allowed window (calendar days) for the amount + date match (L4).
DATE_WINDOW_DAYS = 3


def _stringify(value) -> str:
    return "" if value is None else str(value)


def invoice_number_similarity(a, b) -> float:
    """Fuzzy similarity (0..100) between two invoice numbers.

    Uses RapidFuzz when available — both `token_sort_ratio` (tolerates token
    re-ordering / punctuation such as "INV-1024" vs "INV1024") and `ratio`
    (plain edit-distance similarity) — and reports the higher of the two.
    Falls back to difflib.SequenceMatcher.
    """
    left = _stringify(a).strip()
    right = _stringify(b).strip()

    try:
        from rapidfuzz import fuzz

        token_sort = fuzz.token_sort_ratio(left, right)
        plain_ratio = fuzz.ratio(left, right)
        return round(max(token_sort, plain_ratio), 2)
    except ImportError:  # pragma: no cover - RapidFuzz is a declared dependency
        score = SequenceMatcher(None, left.casefold(), right.casefold()).ratio()
        return round(score * 100.0, 2)


def amounts_equal(a, b, tolerance: float = AMOUNT_EQUAL_TOLERANCE) -> bool:
    """True when two totals are within `tolerance` of each other.

    A tiny epsilon absorbs binary floating-point rounding (e.g. 100.01 - 100.0
    is 0.010000000000005116, not exactly 0.01).
    """
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= tolerance + 1e-9


def amounts_near(a, b, tolerance: float = NEAR_AMOUNT_TOLERANCE) -> bool:
    """True when two totals differ by at most `tolerance` (near duplicate)."""
    return amounts_equal(a, b, tolerance=tolerance)


def dates_equal(a, b) -> bool:
    """True when both dates are set and equal."""
    return a is not None and b is not None and a == b


def dates_close(a, b, max_days: int = DATE_WINDOW_DAYS) -> bool:
    """True when both dates are set and within `max_days` calendar days."""
    if a is None or b is None:
        return False
    return abs((a - b).days) <= max_days


def _item_key(item) -> tuple:
    """Normalised comparable key for one line item (name, qty, unit price)."""
    name = (item.product_name or "General").strip() or "General"
    quantity = round(float(item.quantity or 0), 3)
    unit_price = round(float(item.unit_price or 0), 2)
    return (name.casefold(), quantity, unit_price)


def items_identical(items_a, items_b) -> bool:
    """True when both invoices carry the SAME multiset of line items.

    Order-insensitive; both sides must have at least one line item (so two
    item-less invoices never count as identical by accident).
    """
    left = sorted(_item_key(i) for i in (items_a or []))
    right = sorted(_item_key(i) for i in (items_b or []))
    if not left or not right:
        return False
    return left == right