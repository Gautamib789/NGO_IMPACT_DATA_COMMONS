from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    category = Column(String, nullable=False) # e.g. Equipment, Supplies, Travel, Personnel
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    expense_date = Column(DateTime, default=datetime.utcnow)
    receipt_file_name = Column(String, nullable=True)
    receipt_file_path = Column(String, nullable=True)
    receipt_sha256 = Column(String, nullable=True)
    verification_status = Column(String, default="PENDING", nullable=False) # PENDING, VERIFIED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ngo = relationship("NGODetail", back_populates="expenses")
    project = relationship("Project", back_populates="expenses")
