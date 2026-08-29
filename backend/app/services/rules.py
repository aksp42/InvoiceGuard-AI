"""Individual validation rules (Phase 4: rule-based validation engine).

Every rule is a pure function with the same signature:

    rule(invoice, items, context) -> list[Issue]

  - `invoice`  : the Invoice ORM object being validated
  - `items`    : the invoice's line items (iterable of InvoiceItem)
  - `context`  : a RuleContext carrying shared inputs (today, tolerances)
                 so rules stay deterministic and unit-testable.

Rules only DECIDE. They never touch the database — persistence and invoice
status updates live in validation_service.py, orchestration in validator.py.
"""

from dataclasses import dataclass
from datetime import date

# ---------------------------------------------------------------------------
# Severity levels (must be a subset of validation_results.severity ENUM)
# ---------------------------------------------------------------------------
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"
CRITICAL = "CRITICAL"

# ---------------------------------------------------------------------------
# validation_type codes (must be a subset of schema.sql chk_validation_type)
# ---------------------------------------------------------------------------
MISSING_FIELD = "MISSING_FIELD"
INVALID_DATE = "INVALID_DATE"
FUTURE_DATE = "FUTURE_DATE"
TOTAL_MISMATCH = "TOTAL_MISMATCH"
NEGATIVE_AMOUNT = "NEGATIVE_AMOUNT"
QUANTITY_INVALID = "QUANTITY_INVALID"
UNIT_PRICE_INVALID = "UNIT_PRICE_INVALID"
GST_OUT_OF_RANGE = "GST_OUT_OF_RANGE"
EMPTY_PRODUCT_NAME = "EMPTY_PRODUCT_NAME"


@dataclass
class Issue:
    """A single validation finding: what, how severe, and why."""

    validation_type: str
    severity: str
    message: str


@dataclass
class RuleContext:
    """Shared, injectable inputs for the rule set (today + tolerances)."""

    today: date
    total_tolerance: float = 0.01

    @classmethod
    def default(cls):
        return cls(today=date.today(), total_tolerance=0.01)


def _is_blank(value) -> bool:
    if value is None:
        return True
    return str(value).strip() == ""


def _item_label(item) -> str:
    return (item.product_name or "General").strip() or "General"


# ---------------------------------------------------------------------------
# Rule 1 — Missing Invoice Number (CRITICAL)
# ---------------------------------------------------------------------------
def rule_missing_invoice_number(invoice, items, context) -> list[Issue]:
    if _is_blank(invoice.invoice_number):
        return [Issue(MISSING_FIELD, CRITICAL, "Missing required field: invoice_number.")]
    return []


# ---------------------------------------------------------------------------
# Rule 2 — Missing Vendor Name (CRITICAL)
# ---------------------------------------------------------------------------
def rule_missing_vendor_name(invoice, items, context) -> list[Issue]:
    vendor_name = invoice.vendor.vendor_name if invoice.vendor else None
    if _is_blank(vendor_name):
        return [Issue(MISSING_FIELD, CRITICAL, "Missing required field: vendor_name.")]
    return []


# ---------------------------------------------------------------------------
# Rule 3 — Invalid Invoice Date (ERROR)
# ---------------------------------------------------------------------------
def rule_invalid_invoice_date(invoice, items, context) -> list[Issue]:
    if invoice.invoice_date is None:
        return [Issue(INVALID_DATE, ERROR, "Invoice date is empty or in an invalid format.")]
    return []


# ---------------------------------------------------------------------------
# Rule 4 — Future Invoice Date (WARNING)
# ---------------------------------------------------------------------------
def rule_future_invoice_date(invoice, items, context) -> list[Issue]:
    if invoice.invoice_date is not None and invoice.invoice_date > context.today:
        return [
            Issue(
                FUTURE_DATE,
                WARNING,
                f"Invoice dated in the future: {invoice.invoice_date.isoformat()}.",
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Rule 5 — Negative Amount (CRITICAL) — checks subtotal, tax, total
# ---------------------------------------------------------------------------
def rule_negative_amounts(invoice, items, context) -> list[Issue]:
    issues = []
    for label in ("subtotal", "tax_amount", "total_amount"):
        value = getattr(invoice, label)
        if value is not None and value < 0:
            issues.append(
                Issue(NEGATIVE_AMOUNT, CRITICAL, f"Negative amount detected: {label}={value}.")
            )
    return issues


# ---------------------------------------------------------------------------
# Rule 6 — Quantity Validation (ERROR): must be greater than zero
# ---------------------------------------------------------------------------
def rule_quantity_positive(invoice, items, context) -> list[Issue]:
    issues = []
    for item in items:
        if item.quantity is None or item.quantity <= 0:
            issues.append(
                Issue(
                    QUANTITY_INVALID,
                    ERROR,
                    f"Line-item quantity must be greater than zero: "
                    f"'{_item_label(item)}' (quantity={item.quantity}).",
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Rule 7 — Unit Price Validation (ERROR): must be greater than zero
# ---------------------------------------------------------------------------
def rule_unit_price_positive(invoice, items, context) -> list[Issue]:
    issues = []
    for item in items:
        if item.unit_price is None or item.unit_price <= 0:
            issues.append(
                Issue(
                    UNIT_PRICE_INVALID,
                    ERROR,
                    f"Line-item unit price must be greater than zero: "
                    f"'{_item_label(item)}' (unit_price={item.unit_price}).",
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Rule 8 — GST Range (ERROR): allowed 0–100
# ---------------------------------------------------------------------------
def rule_gst_range(invoice, items, context) -> list[Issue]:
    issues = []
    for item in items:
        if item.tax_percent is None or not (0 <= item.tax_percent <= 100):
            issues.append(
                Issue(
                    GST_OUT_OF_RANGE,
                    ERROR,
                    f"GST rate out of allowed range 0-100: "
                    f"'{_item_label(item)}' (gst_percent={item.tax_percent}).",
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Rule 9 — Total Calculation (CRITICAL): Total = Subtotal + Tax (± tolerance)
# ---------------------------------------------------------------------------
def rule_total_consistency(invoice, items, context) -> list[Issue]:
    if invoice.subtotal is None or invoice.tax_amount is None or invoice.total_amount is None:
        return [
            Issue(
                TOTAL_MISMATCH,
                CRITICAL,
                "Cannot verify total: subtotal, tax_amount or total_amount is missing "
                f"(subtotal={invoice.subtotal}, tax_amount={invoice.tax_amount}, "
                f"total_amount={invoice.total_amount}).",
            )
        ]
    expected = round(invoice.subtotal + invoice.tax_amount + 1e-9, 2)
    if abs(expected - invoice.total_amount) > context.total_tolerance:
        return [
            Issue(
                TOTAL_MISMATCH,
                CRITICAL,
                f"Total mismatch: expected {expected}, got {invoice.total_amount} "
                f"(tolerance {context.total_tolerance}).",
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Rule 10 — Empty Product Name (WARNING)
# ---------------------------------------------------------------------------
def rule_empty_product_name(invoice, items, context) -> list[Issue]:
    issues = []
    for item in items:
        if _is_blank(item.product_name):
            issues.append(
                Issue(
                    EMPTY_PRODUCT_NAME,
                    WARNING,
                    "Line item has an empty product name; supplier data is incomplete for reporting.",
                )
            )
    return issues


# Ordered rule registry — validator.py runs them in exactly this order.
ALL_RULES = [
    rule_missing_invoice_number,
    rule_missing_vendor_name,
    rule_invalid_invoice_date,
    rule_future_invoice_date,
    rule_negative_amounts,
    rule_quantity_positive,
    rule_unit_price_positive,
    rule_gst_range,
    rule_total_consistency,
    rule_empty_product_name,
]