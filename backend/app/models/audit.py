from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=True)
    action = Column(String, nullable=False) # e.g. PROFILE_UPDATE, DOC_UPLOAD, GOV_VERIFY, PROJECT_CREATE
    entity_type = Column(String, nullable=False) # e.g. NGO, DOCUMENT, PROJECT, EXPENSE
    entity_id = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    actor = relationship("User", back_populates="audit_logs")
    ngo = relationship("NGODetail", back_populates="audit_logs")
