from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    donor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    donor_name = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    transaction_hash = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="COMPLETED") # COMPLETED, FLAGGED
    created_at = Column(DateTime, default=datetime.utcnow)

    donor = relationship("User", back_populates="donations")
    ngo = relationship("NGODetail", back_populates="donations")
