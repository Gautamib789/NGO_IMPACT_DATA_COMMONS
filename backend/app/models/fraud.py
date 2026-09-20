from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id = Column(Integer, primary_key=True, index=True)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=False)
    severity = Column(String, nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    rule_code = Column(String, nullable=False) # e.g. EXPENSE_OVER_DONATION, DOC_MISSING, HIGH_VELOCITY
    description = Column(Text, nullable=False)
    status = Column(String, default="OPEN") # OPEN, RESOLVED, DISMISSED
    created_at = Column(DateTime, default=datetime.utcnow)

    ngo = relationship("NGODetail", back_populates="fraud_flags")
