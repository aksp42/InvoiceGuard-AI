"""Validation result model — matches `validation_results` in database/schema.sql.

One row per rule issue raised for an invoice (Phase 4: rule-based validation
engine). confidence_score stays NULL for the deterministic rules — it is only
populated by future ML-based flags.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base


class ValidationResult(Base):
    __tablename__ = "validation_results"

    validation_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"), nullable=False)
    validation_type = Column(String(50), nullable=False)
    severity = Column(String(32), default="WARNING")  # INFO / WARNING / ERROR / CRITICAL
    message = Column(String(500), nullable=False)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="validations")