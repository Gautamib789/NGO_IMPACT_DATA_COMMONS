from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- Project Schemas ---
class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, description="Name of the project")
    description: Optional[str] = None
    category: str = Field("General", description="Category of the project (e.g., Education, Health, Environment)")
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    budget: float = Field(..., gt=0, description="Project budget amount (must be positive)")
    target_beneficiaries: int = Field(0, ge=0, description="Target number of beneficiaries")
    outcomes: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    budget: Optional[float] = Field(None, gt=0)
    target_beneficiaries: Optional[int] = Field(None, ge=0)
    outcomes: Optional[str] = None
    status: Optional[str] = None

class ProjectOut(BaseModel):
    id: int
    ngo_id: int
    project_name: str
    description: Optional[str] = None
    category: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: float
    target_beneficiaries: int
    total_expenses_claimed: float = 0.0
    fund_utilization_ratio: float = 0.0
    beneficiary_count: int = 0
    outcomes: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Beneficiary Schemas ---
class BeneficiaryCreate(BaseModel):
    project_id: Optional[int] = None
    beneficiary_code: Optional[str] = Field(None, description="Masked fictional identifier, e.g. BEN-2026-001. Generated if omitted.")
    name_or_alias: str = Field(..., min_length=1, description="Alias or pseudonym for privacy protection")
    age_group: Optional[str] = Field("Adults", description="Age group (Children, Youth, Adults, Seniors)")
    gender: Optional[str] = None
    location: Optional[str] = None

class BeneficiaryOut(BaseModel):
    id: int
    ngo_id: int
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    beneficiary_code: str
    name_or_alias: str
    age_group: Optional[str] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Expense & Receipt Schemas ---
class ExpenseCreate(BaseModel):
    project_id: Optional[int] = None
    category: str = Field(..., min_length=1, description="Expense category (e.g. Equipment, Supplies, Travel, Personnel)")
    description: Optional[str] = None
    amount: float = Field(..., gt=0, description="Expense amount (must be positive)")

class ExpenseOut(BaseModel):
    id: int
    ngo_id: int
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    category: str
    description: Optional[str] = None
    amount: float
    expense_date: datetime
    receipt_file_name: Optional[str] = None
    receipt_file_path: Optional[str] = None
    receipt_sha256: Optional[str] = None
    verification_status: str
    created_at: datetime

    class Config:
        from_attributes = True
