from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ExpenseCreate(BaseModel):
    project_id: Optional[int] = None
    category: str
    description: Optional[str] = None
    amount: float
    expense_date: Optional[datetime] = None
    receipt_file_name: Optional[str] = None
    receipt_file_path: Optional[str] = None
    receipt_sha256: Optional[str] = None

class ExpenseUpdate(BaseModel):
    project_id: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    expense_date: Optional[datetime] = None
    verification_status: Optional[str] = None

class ExpenseOut(BaseModel):
    id: int
    ngo_id: int
    project_id: Optional[int] = None
    category: str
    description: Optional[str] = None
    amount: float
    expense_date: datetime
    receipt_file_name: Optional[str] = None
    receipt_file_path: Optional[str] = None
    receipt_sha256: Optional[str] = None
    verification_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
