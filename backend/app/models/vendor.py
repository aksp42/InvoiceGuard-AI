"""Vendor model — matches `vendors` in database/schema.sql."""
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"))
    vendor_name = Column(String(255), nullable=False)
    gst_number = Column(String(32))

    invoices = relationship("Invoice", back_populates="vendor")