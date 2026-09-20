from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditLogOut(BaseModel):
    id: int
    actor_user_id: Optional[int] = None
    ngo_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    metadata_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
