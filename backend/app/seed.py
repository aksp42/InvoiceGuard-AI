"""
Development auto-seeding (Phase 6.1: production readiness).

Inserts a small, representative sample dataset the FIRST time the database is
empty so that a fresh clone can immediately explore the Executive Dashboard.

Guarantees:
  - NEVER overwrites existing data (only seeds when the invoices table is empty)
  - controlled by the `AUTO_SEED` setting (defaults to on for development)
  - works against both SQLite and MySQL (pure ORM, no raw SQL dialect)
  - every decision path is logged (seeded / skipped-and-empty / skipped-has-data)
"""
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.logging_config import get_logger
from backend.app.models import Company, Invoice, InvoiceItem, UploadBatch, Vendor

logger = get_logger()

_DEFAULT_COMPANY = (1, "Akshu Enterprises Pvt Ltd", "27AACCA9603R1ZM", "accounts@akshuenterprises.com")


def _seed_company(db: Session) -> Company:
    """Ensure the default company exists (idempotent)."""
    company = db.query(Company).filter_by(company_id=_DEFAULT_COMPANY[0]).first()
    if company is None:
        company = Company(
            company_id=_DEFAULT_COMPANY[0],
            company_name=_DEFAULT_COMPANY[1],
            gst_number=_DEFAULT_COMPANY[2],
            email=_DEFAULT_COMPANY[3],
        )
        db.add(company)
        db.flush()
    return company


def _build_sample() -> list[dict]:
    """Return the sample dataset: vendors, invoices (+ items) and one batch."""
    today = date.today()
    vendors = [
        {"name": "Acme Traders", "gst": "07AAACP1234F1Z5"},
        {"name": "Globex Supplies", "gst": "24AAACG5678K1Z2"},
        {"name": "Initech Solutions", "gst": "29AAACI9012L1Z9"},
        {"name": "Umbrella Corp", "gst": "08AAAUC3456M1Z8"},
    ]
    invoices = [
        # number, vendor_idx, date_offset, subtotal, tax, status, risk
        {"num": "ACME-2026-001", "vendor": 0, "days": 0, "sub": 120000, "tax": 12000, "status": "Valid", "risk": 5, "items": [("Consumables", 40, 3000, 10)]},
        {"num": "ACME-2026-002", "vendor": 0, "days": 3, "sub": 84500, "tax": 8450, "status": "Valid", "risk": 8, "items": [("Spare Parts", 25, 3380, 10)]},
        {"num": "GLOBEX-2026-014", "vendor": 1, "days": 1, "sub": 56000, "tax": 8960, "status": "Needs Review", "risk": 42, "items": [("Electronics", 10, 5600, 16)]},
        {"num": "GLOBEX-2026-015", "vendor": 1, "days": 2, "sub": 56000, "tax": 8960, "status": "Needs Review", "risk": 44, "items": [("Electronics", 10, 5600, 16)]},
        {"num": "INITECH-2026-077", "vendor": 2, "days": 4, "sub": 210000, "tax": 25200, "status": "High Risk", "risk": 78, "items": [("Machinery", 3, 70000, 12)]},
        {"num": "INITECH-2026-078", "vendor": 2, "days": 5, "sub": 33500, "tax": 4020, "status": "Valid", "risk": 12, "items": [("Labware", 12, 2791.67, 12)]},
        {"num": "UMBRELLA-2026-036", "vendor": 3, "days": 6, "sub": 98000, "tax": 17640, "status": "Critical", "risk": 91, "items": [("Special Equipment", 4, 24500, 18)]},
    ]
    return {"vendors": vendors, "invoices": invoices, "today": today}


def maybe_seed(db: Session) -> bool:
    """Seed sample data if the database is empty and auto-seed is enabled.

    Returns True when seed data is present afterwards (seeded or already there).
    """
    if not settings.auto_seed:
        logger.info("Seed skipped: auto-seed is disabled.")
        return True

    # Only seed when there is no invoice data (never overwrite real data).
    existing = db.query(Invoice).count()
    if existing > 0:
        logger.info("Seed skipped: database already contains %d invoice(s).", existing)
        return True

    sample = _build_sample()
    try:
        _seed_company(db)
        vendor_rows = []
        for v in sample["vendors"]:
            vrow = Vendor(company_id=_DEFAULT_COMPANY[0], vendor_name=v["name"], gst_number=v["gst"])
            db.add(vrow)
            vendor_rows.append(vrow)
        db.flush()

        batch = UploadBatch(
            file_name="seed_sample.csv",
            uploaded_by=settings.demo_user,
            status="Completed",
            total_invoices=len(sample["invoices"]),
            processed_invoices=len(sample["invoices"]),
            failed_invoices=0,
        )
        db.add(batch)
        db.flush()

        for inv in sample["invoices"]:
            invoice_date = sample["today"] - timedelta(days=inv["days"])
            row = Invoice(
                company_id=_DEFAULT_COMPANY[0],
                vendor_id=vendor_rows[inv["vendor"]].vendor_id,
                invoice_number=inv["num"],
                batch_id=batch.batch_id,
                invoice_date=invoice_date,
                subtotal=inv["sub"],
                tax_amount=inv["tax"],
                total_amount=inv["sub"] + inv["tax"],
                risk_score=inv["risk"],
                status=inv["status"],
            )
            db.add(row)
            db.flush()
            for (product, qty, price, tax) in inv["items"]:
                db.add(InvoiceItem(
                    invoice_id=row.invoice_id,
                    product_name=product,
                    quantity=qty,
                    unit_price=price,
                    tax_percent=tax,
                    line_total=round(qty * price * (1 + tax / 100), 2),
                ))

        db.commit()
        count = db.query(Invoice).count()
        logger.info(
            "Seed completed: inserted %d invoice(s), %d vendor(s), 1 batch.",
            count, len(vendor_rows),
        )
        return True
    except Exception:  # pragma: no cover - infra dependent
        db.rollback()
        logger.exception("Seed failed; rolled back. Dashboard will start empty.")
        return False


def is_seeded(db: Session) -> bool:
    """Return True if the database already contains invoice data."""
    try:
        return db.query(Invoice).count() > 0
    except Exception:  # pragma: no cover - infra dependent
        return False
