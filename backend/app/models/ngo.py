import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class NGOStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class NGODetail(Base):
    __tablename__ = "ngo_details"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    org_name = Column(String, index=True, nullable=False)
    registration_number = Column(String, unique=True, nullable=False)
    tax_id = Column(String, nullable=False)
    category = Column(String, nullable=False, default="General Social Welfare")
    mission_statement = Column(Text, nullable=True)
    website = Column(String, nullable=True)
    address = Column(String, nullable=True)
    status = Column(Enum(NGOStatus), default=NGOStatus.PENDING, nullable=False)
    
    doc_completeness_score = Column(Float, default=0.0) # 0-100%
    transparency_score = Column(Float, default=50.0) # 0-100%
    
    total_expenses = Column(Float, default=0.0)
    total_donations_received = Column(Float, default=0.0)
    beneficiary_count = Column(Integer, default=0)
    rejection_reason = Column(Text, nullable=True)

    # Extended Profile Fields (Phase 2 Non-Breaking Addition)
    established_date = Column(DateTime, nullable=True)
    organization_type = Column(String, nullable=True, default="Trust")
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    pin_code = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    vision = Column(Text, nullable=True)
    operating_areas = Column(Text, nullable=True)
    pan = Column(String, nullable=True)
    eighty_g_info = Column(String, nullable=True)
    fcra_info = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    government_verification_status = Column(String, default="NOT_VERIFIED", nullable=False) # e.g. VERIFIED, PARTIALLY_MATCHED, NOT_VERIFIED, INACTIVE
    risk_level = Column(String, default="LOW", nullable=False) # e.g. LOW, MEDIUM, HIGH, CRITICAL
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="ngo_detail")
    documents = relationship("NGODocument", back_populates="ngo", cascade="all, delete-orphan")
    donations = relationship("Donation", back_populates="ngo")
    fraud_flags = relationship("FraudFlag", back_populates="ngo", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="ngo", cascade="all, delete-orphan")
    beneficiaries = relationship("Beneficiary", back_populates="ngo", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="ngo", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="ngo", cascade="all, delete-orphan")


class NGODocument(Base):
    __tablename__ = "ngo_documents"

    id = Column(Integer, primary_key=True, index=True)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=False)
    document_type = Column(String, nullable=False) # e.g., Audit Report, Tax Certificate, ID Proof, 80G, FCRA, Invoice
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)

    # Document Integrity & Verification Fields (Phase 2 Non-Breaking Addition)
    sha256_hash = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    verification_status = Column(String, default="PROCESSING", nullable=False) # PROCESSING, VERIFIED, LOW_RISK, NEEDS_ADMIN_REVIEW, REJECTED, EXPIRED
    verification_message = Column(Text, nullable=True)
    tamper_risk_score = Column(Float, default=0.0, nullable=False) # 0 to 100
    tamper_risk_level = Column(String, default="LOW", nullable=False) # LOW, MEDIUM, HIGH
    ocr_text = Column(Text, nullable=True)
    exif_metadata = Column(Text, nullable=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    capture_timestamp = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    ngo = relationship("NGODetail", back_populates="documents")
