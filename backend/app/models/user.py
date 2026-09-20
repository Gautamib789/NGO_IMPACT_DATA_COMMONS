import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    NGO = "NGO"
    DONOR = "DONOR"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.DONOR, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    ngo_detail = relationship("NGODetail", back_populates="user", uselist=False, cascade="all, delete-orphan")
    donations = relationship("Donation", back_populates="donor")
    audit_logs = relationship("AuditLog", back_populates="actor")
