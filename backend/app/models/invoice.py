"""Invoice header model — matches `invoices` in database/schema.sql (Phase 2.1).

invoice_id is an INT surrogate key (changed from the legacy VARCHAR id).
Deliberately uses an indexed, non-unique invoice_number so duplicate
submissions can be stored and flagged in a later phase.
"""
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"))
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"))
    invoice_number = Column(String(64), nullable=False)
    batch_id = Column(Integer, ForeignKey("upload_batches.batch_id"), nullable=True)
    invoice_date = Column(Date, nullable=False)
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    status = Column(String(32), default="Pending")  # Pending / Valid / Needs Review / High Risk / Duplicate / Paid

    vendor = relationship("Vendor", back_populates="invoices")
    batch = relationship("UploadBatch", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice")
    validations = relationship(
        "ValidationResult",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )