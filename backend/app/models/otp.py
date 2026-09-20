import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class OTPPurpose(str, enum.Enum):
    LOGIN = "LOGIN"
    RESET_PASSWORD = "RESET_PASSWORD"


class OtpCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose = Column(Enum(OTPPurpose), nullable=False)
    hashed_otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempt_count = Column(Integer, default=0, nullable=False)
    resend_count = Column(Integer, default=0, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User")
