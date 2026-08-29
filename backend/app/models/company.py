"""Company (tenant) model — matches `companies` in database/schema.sql."""
from sqlalchemy import Column, Integer, String

from backend.app.database import Base


class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    gst_number = Column(String(32), nullable=False)
    email = Column(String(255), nullable=False)