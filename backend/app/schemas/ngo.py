from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from app.models.ngo import NGOStatus


class NGOCreate(BaseModel):
    org_name: str
    registration_number: str
    tax_id: str
    category: str = "General Social Welfare"
    mission_statement: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    established_date: Optional[datetime] = None
    organization_type: Optional[str] = "Trust"
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    pin_code: Optional[str] = None
    phone: Optional[str] = None
    vision: Optional[str] = None
    operating_areas: Optional[str] = None
    pan: Optional[str] = None
    eighty_g_info: Optional[str] = None
    fcra_info: Optional[str] = None
    gst_number: Optional[str] = None


class NGOUpdate(BaseModel):
    org_name: Optional[str] = None
    category: Optional[str] = None
    mission_statement: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    established_date: Optional[datetime] = None
    organization_type: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    pin_code: Optional[str] = None
    phone: Optional[str] = None
    vision: Optional[str] = None
    operating_areas: Optional[str] = None
    pan: Optional[str] = None
    eighty_g_info: Optional[str] = None
    fcra_info: Optional[str] = None
    gst_number: Optional[str] = None


class NGODocumentOut(BaseModel):
    id: int
    ngo_id: int
    document_type: str
    file_name: str
    file_path: str
    upload_date: datetime
    sha256_hash: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    verification_status: str = "PROCESSING"
    verification_message: Optional[str] = None
    tamper_risk_score: float = 0.0
    tamper_risk_level: str = "LOW"
    ocr_text: Optional[str] = None
    exif_metadata: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    capture_timestamp: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    class Config:
        from_attributes = True


class NGOOut(BaseModel):
    id: int
    user_id: int
    org_name: str
    registration_number: str
    tax_id: str
    category: str
    mission_statement: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    status: NGOStatus
    doc_completeness_score: float
    transparency_score: float
    total_expenses: float
    total_donations_received: float
    beneficiary_count: int
    rejection_reason: Optional[str] = None
    established_date: Optional[datetime] = None
    organization_type: Optional[str] = "Trust"
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    pin_code: Optional[str] = None
    phone: Optional[str] = None
    vision: Optional[str] = None
    operating_areas: Optional[str] = None
    pan: Optional[str] = None
    eighty_g_info: Optional[str] = None
    fcra_info: Optional[str] = None
    gst_number: Optional[str] = None
    government_verification_status: str = "NOT_VERIFIED"
    risk_level: str = "LOW"
    created_at: datetime
    documents: List[NGODocumentOut] = []

    class Config:
        from_attributes = True


class PublicNGODocumentOut(BaseModel):
    id: int
    ngo_id: int
    document_type: str
    file_name: str
    upload_date: datetime
    sha256_hash: Optional[str] = None
    verification_status: str = "PROCESSING"
    tamper_risk_level: str = "LOW"

    class Config:
        from_attributes = True


class PublicNGOOut(BaseModel):
    id: int
    org_name: str
    registration_number: str
    tax_id: str
    category: str
    mission_statement: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    status: NGOStatus
    doc_completeness_score: float
    transparency_score: float
    total_expenses: float
    total_donations_received: float
    beneficiary_count: int
    established_date: Optional[datetime] = None
    organization_type: Optional[str] = "Trust"
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    pin_code: Optional[str] = None
    vision: Optional[str] = None
    operating_areas: Optional[str] = None
    government_verification_status: str = "NOT_VERIFIED"
    risk_level: str = "LOW"
    created_at: datetime
    documents: List[PublicNGODocumentOut] = []

    class Config:
        from_attributes = True


class NGOFinancialUpdate(BaseModel):
    total_expenses: float
    total_donations_received: float
    beneficiary_count: int
