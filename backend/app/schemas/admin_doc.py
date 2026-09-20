from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class AdminDocReviewIn(BaseModel):
    decision: str = Field(..., description="Decision must be APPROVE, REJECT, or REQUEST_CLARIFICATION")
    notes: Optional[str] = Field(None, description="Optional review notes from the administrator")

class AdminDocInspectionOut(BaseModel):
    id: int
    ngo_id: int
    ngo_org_name: Optional[str] = None
    ngo_registration_number: Optional[str] = None
    document_type: str
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    sha256_hash: Optional[str] = None
    verification_status: str
    verification_message: Optional[str] = None
    tamper_risk_score: Optional[float] = 0.0
    tamper_risk_level: Optional[str] = "LOW"
    ocr_text: Optional[str] = None
    exif_metadata: Optional[str] = None
    upload_date: datetime
    reviewed_by: Optional[int] = None
    reviewed_by_email: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    audit_history: List[Any] = []

    class Config:
        from_attributes = True
