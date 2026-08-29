"""
GST / tax calculation helpers (project report, section "Total / GST verification").

Expected total = (quantity x unit price) + GST% on the subtotal.
"""
from backend.app.config import AMOUNT_TOLERANCE


def expected_total(quantity: float, unit_price: float, gst_percent: float) -> float:
    """Return the expected invoice total for a line at the given GST rate."""
    subtotal = quantity * unit_price
    return round(subtotal + subtotal * (gst_percent / 100.0), 2)


def total_mismatches(
    quantity, unit_price, gst_percent, total_amount, tolerance: float = AMOUNT_TOLERANCE
) -> bool:
    """True when the reported total differs from the calculated one by > tolerance (rupees)."""
    try:
        exp = expected_total(float(quantity), float(unit_price), float(gst_percent or 0))
    except (TypeError, ValueError):
        return False
    return abs(exp - float(total_amount)) > tolerance