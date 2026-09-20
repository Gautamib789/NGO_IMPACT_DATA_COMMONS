# DEMO GOVERNMENT REGISTRY MODEL
# NOTE: This model represents a simulated demo government registry for academic/project demonstration only.
# It does NOT connect to a live government database or store real personal data.

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class GovernmentRegistry(Base):
    __tablename__ = "government_registry"

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String, unique=True, index=True, nullable=False)
    org_name = Column(String, nullable=False)
    pan = Column(String, nullable=True)
    eighty_g_info = Column(String, nullable=True)
    fcra_info = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    organization_type = Column(String, nullable=True, default="Trust")
    status = Column(String, default="ACTIVE", nullable=False) # e.g. ACTIVE, INACTIVE, SUSPENDED
    registered_state = Column(String, nullable=True)
    registered_district = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
