"""Invoice read endpoints (data persisted in the DB by uploads)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.invoice import Invoice

router = APIRouter(prefix="/api", tags=["invoices"])


@router.get("/invoices")
def list_invoices(db: Session = Depends(get_db)):
    rows = db.query(Invoice).order_by(Invoice.invoice_date.desc()).all()
    return [
        {
            "invoice_id": i.invoice_id,
            "invoice_date": i.invoice_date.isoformat() if i.invoice_date else None,
            "total_amount": i.total_amount,
            "risk_score": i.risk_score,
            "status": i.status,
            "vendor_name": i.vendor.vendor_name if i.vendor else None,
        }
        for i in rows
    ]


@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if inv is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "invoice_id": inv.invoice_id,
        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
        "total_amount": inv.total_amount,
        "risk_score": inv.risk_score,
        "status": inv.status,
        "vendor": {
            "vendor_id": inv.vendor.vendor_id if inv.vendor else None,
            "vendor_name": inv.vendor.vendor_name if inv.vendor else None,
            "gst_number": inv.vendor.gst_number if inv.vendor else None,
        },
        "items": [
            {"product_name": it.product_name, "quantity": it.quantity, "unit_price": it.unit_price}
            for it in (inv.items or [])
        ],
    }