from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=False)
    project_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False, default="General")
    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    objective = Column(Text, nullable=True)
    target_beneficiaries = Column(String, nullable=True)
    number_of_beneficiaries = Column(Integer, default=0, nullable=False)
    
    # Financial Fields
    total_budget = Column(Float, default=0.0, nullable=False)
    funding_received = Column(Float, default=0.0, nullable=False)
    amount_spent = Column(Float, default=0.0, nullable=False)
    remaining_amount = Column(Float, default=0.0, nullable=False)
    ngo_contribution = Column(Float, default=0.0, nullable=False)
    donor_funding = Column(Float, default=0.0, nullable=False)
    government_funding = Column(Float, default=0.0, nullable=False)
    
    status = Column(String, default="ACTIVE", nullable=False) # DRAFT, SUBMITTED, ACTIVE, COMPLETED, SUSPENDED, REJECTED
    contact_person = Column(String, nullable=True)
    
    # Risk & Verification Summary
    integrity_status = Column(String, default="VERIFIED", nullable=False) # VERIFIED, NEEDS_ADMIN_REVIEW, REJECTED
    risk_score = Column(Float, default=0.0, nullable=False) # 0 to 100%
    risk_level = Column(String, default="LOW", nullable=False) # LOW, MEDIUM, HIGH
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ngo = relationship("NGODetail", back_populates="projects")
    beneficiaries = relationship("Beneficiary", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="project", cascade="all, delete-orphan")
    project_expenses = relationship("ProjectExpense", back_populates="project", cascade="all, delete-orphan")
    evidence_files = relationship("ProjectEvidence", back_populates="project", cascade="all, delete-orphan")
    risk_analyses = relationship("ProjectRiskAnalysis", back_populates="project", cascade="all, delete-orphan")
    findings = relationship("ProjectFinding", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("AdminProjectReview", back_populates="project", cascade="all, delete-orphan")
    notifications = relationship("AdminNotification", back_populates="project", cascade="all, delete-orphan")



class ProjectEvidence(Base):
    __tablename__ = "project_evidence"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=False)
    evidence_type = Column(String, nullable=False) # BEFORE_PHOTO, DURING_PHOTO, AFTER_PHOTO, INVOICE, RECEIPT, SITE_PHOTO, COMPLETION_CERT, etc.
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    sha256_hash = Column(String, nullable=False, index=True)
    p_hash = Column(String, nullable=True, index=True) # Perceptual hash for visual similarity
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    ocr_text = Column(Text, nullable=True)
    exif_metadata = Column(Text, nullable=True) # JSON string
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    
    tamper_risk_score = Column(Float, default=0.0, nullable=False)
    tamper_risk_level = Column(String, default="LOW", nullable=False)
    verification_status = Column(String, default="VERIFIED", nullable=False)
    evidence_findings = Column(Text, nullable=True) # JSON list of reasons/findings

    project = relationship("Project", back_populates="evidence_files")
    expenses = relationship("ProjectExpense", back_populates="evidence")


class ProjectExpense(Base):
    __tablename__ = "project_expenses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=False)
    evidence_id = Column(Integer, ForeignKey("project_evidence.id"), nullable=True)
    invoice_number = Column(String, nullable=True, index=True)
    vendor_name = Column(String, nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    expense_date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)
    
    ocr_amount = Column(Float, nullable=True)
    ocr_vendor = Column(String, nullable=True)
    is_ocr_matched = Column(Boolean, default=True)
    discrepancy_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="project_expenses")
    evidence = relationship("ProjectEvidence", back_populates="expenses")


class ProjectRiskAnalysis(Base):
    __tablename__ = "project_risk_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False) # 0 to 100%
    risk_level = Column(String, default="LOW", nullable=False) # LOW, MEDIUM, HIGH
    status = Column(String, default="VERIFIED", nullable=False) # VERIFIED, NEEDS_ADMIN_REVIEW, REJECTED
    
    document_identity_risk = Column(Float, default=0.0)
    photo_integrity_risk = Column(Float, default=0.0)
    financial_integrity_risk = Column(Float, default=0.0)
    evidence_consistency_risk = Column(Float, default=0.0)
    
    findings_json = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="risk_analyses")


class ProjectFinding(Base):
    __tablename__ = "project_findings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    evidence_id = Column(Integer, ForeignKey("project_evidence.id"), nullable=True)
    category = Column(String, nullable=False) # DOCUMENT_IDENTITY, PHOTO_TAMPER, FINANCIAL_FRAUD, EVIDENCE_CONSISTENCY
    risk_level = Column(String, default="LOW", nullable=False) # LOW, MEDIUM, HIGH
    score_impact = Column(Float, default=0.0)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="findings")


class AdminProjectReview(Base):
    __tablename__ = "admin_project_reviews"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    decision = Column(String, nullable=False) # APPROVED, REJECTED, CLARIFICATION_REQUESTED
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="reviews")


class AdminNotification(Base):
    __tablename__ = "admin_notifications"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    ngo_id = Column(Integer, ForeignKey("ngo_details.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default="LOW")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="notifications")

