from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BeneficiaryCreate(BaseModel):
    project_id: Optional[int] = None
    beneficiary_code: str
    name_or_alias: str
    age_group: Optional[str] = None
    gender: Optional[str] = None
    location: Optional[str] = None

class BeneficiaryUpdate(BaseModel):
    project_id: Optional[int] = None
    beneficiary_code: Optional[str] = None
    name_or_alias: Optional[str] = None
    age_group: Optional[str] = None
    gender: Optional[str] = None
    location: Optional[str] = None

class BeneficiaryOut(BaseModel):
    id: int
    ngo_id: int
    project_id: Optional[int] = None
    beneficiary_code: str
    name_or_alias: str
    age_group: Optional[str] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
