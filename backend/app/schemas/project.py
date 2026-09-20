from pydantic import BaseModel, computed_field, field_validator
from typing import Optional, List, Union
from datetime import datetime

class ProjectCreateSchema(BaseModel):
    project_name: str
    description: Optional[str] = None
    category: Optional[str] = "General"
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    objective: Optional[str] = None
    outcomes: Optional[str] = None
    target_beneficiaries: Optional[Union[str, int]] = None
    number_of_beneficiaries: Optional[int] = None
    budget: Optional[float] = None
    total_budget: Optional[float] = None
    funding_received: Optional[float] = 0.0
    ngo_contribution: Optional[float] = 0.0
    donor_funding: Optional[float] = 0.0
    government_funding: Optional[float] = 0.0
    contact_person: Optional[str] = None
    status: Optional[str] = "ACTIVE"

    @field_validator("project_name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Project name is required")
        return v.strip()

    class Config:
        from_attributes = True

class ExpenseCreateSchema(BaseModel):
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    amount: float
    expense_date: Optional[str] = None
    description: Optional[str] = None
    evidence_id: Optional[int] = None

    class Config:
        from_attributes = True

class ProjectOutSchema(BaseModel):
    id: int
    ngo_id: int
    project_name: str
    description: Optional[str] = None
    category: Optional[str] = "General"
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    objective: Optional[str] = None
    target_beneficiaries: Optional[Union[str, int]] = None
    number_of_beneficiaries: Optional[int] = 0
    total_budget: Optional[float] = 0.0
    funding_received: Optional[float] = 0.0
    amount_spent: Optional[float] = 0.0
    remaining_amount: Optional[float] = 0.0
    ngo_contribution: Optional[float] = 0.0
    donor_funding: Optional[float] = 0.0
    government_funding: Optional[float] = 0.0
    contact_person: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    integrity_status: Optional[str] = "VERIFIED"
    risk_score: Optional[float] = 0.0
    risk_level: Optional[str] = "LOW"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @computed_field
    @property
    def budget(self) -> float:
        return float(self.total_budget or 0.0)

    @computed_field
    @property
    def total_expenses_claimed(self) -> float:
        return float(self.amount_spent or 0.0)

    @computed_field
    @property
    def beneficiary_count(self) -> int:
        return int(self.number_of_beneficiaries or 0)

    @computed_field
    @property
    def fund_utilization_ratio(self) -> float:
        tot = float(self.total_budget or 0.0)
        spent = float(self.amount_spent or 0.0)
        if tot > 0:
            return round((spent / tot) * 100.0, 1)
        return 0.0

    @computed_field
    @property
    def outcomes(self) -> Optional[str]:
        return self.objective

    class Config:
        from_attributes = True

