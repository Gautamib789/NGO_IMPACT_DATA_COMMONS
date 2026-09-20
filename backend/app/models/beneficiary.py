# PRIVACY NOTICE: Uses masked/fictional beneficiary identifiers for demonstration. No sensitive personal data (e.g. Aadhaar) is stored.

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(Integer, primary_key=True, index=True)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    beneficiary_code = Column(String, nullable=False, index=True) # Fictional masked code, e.g. BEN-2026-001
    name_or_alias = Column(String, nullable=False)
    age_group = Column(String, nullable=True) # e.g. Children, Youth, Adults, Seniors
    gender = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ngo = relationship("NGODetail", back_populates="beneficiaries")
    project = relationship("Project", back_populates="beneficiaries")
