"""Invoice line-item model — matches `invoice_items` in database/schema.sql.

line_total is computed by the upload pipeline (qty x price x (1 + gst%)).
"""
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.invoice_id"), nullable=False)
    product_name = Column(String(255), default="General")
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    tax_percent = Column(Float, default=0.0)
    line_total = Column(Float, default=0.0)

    invoice = relationship("Invoice", back_populates="items")