from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class GovernmentRegistryOut(BaseModel):
    id: int
    registration_number: str
    org_name: str
    pan: Optional[str] = None
    eighty_g_info: Optional[str] = None
    fcra_info: Optional[str] = None
    gst_number: Optional[str] = None
    organization_type: Optional[str] = "Trust"
    status: str = "ACTIVE"
    registered_state: Optional[str] = None
    registered_district: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FieldMatches(BaseModel):
    registration_number: bool
    org_name: bool
    pan: bool
    eighty_g_info: bool
    fcra_info: bool
    gst_number: bool


class GovernmentVerificationResponse(BaseModel):
    disclaimer: str
    verified_at: str
    registration_number: str
    verification_status: str
    government_match_score: float
    matched_registry_org_name: Optional[str] = None
    matched_registry_state: Optional[str] = None
    field_matches: FieldMatches
    verification_notes: str
