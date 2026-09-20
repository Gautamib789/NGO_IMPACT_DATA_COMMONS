from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DonationCreate(BaseModel):
    ngo_id: int
    amount: float
    currency: str = "INR"
    donor_name: Optional[str] = "Verified Donor"
    message: Optional[str] = None


class DonationOut(BaseModel):
    id: int
    donor_id: int
    ngo_id: int
    amount: float
    currency: str
    donor_name: Optional[str]
    message: Optional[str]
    transaction_hash: str
    status: str
    created_at: datetime
    ngo_name: Optional[str] = None

    class Config:
        from_attributes = True
