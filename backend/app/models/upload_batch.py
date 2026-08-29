"""Upload batch model — matches `upload_batches` in database/schema.sql.

Tracks a single file upload job: which file was uploaded, by whom, when,
and how many invoices were processed / failed (Phase 3: upload pipeline).
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    uploaded_by = Column(String(64), default="admin")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    total_invoices = Column(Integer, default=0)
    processed_invoices = Column(Integer, default=0)
    failed_invoices = Column(Integer, default=0)
    status = Column(String(32), default="Processing")  # Processing / Completed / Failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoices = relationship("Invoice", back_populates="batch")