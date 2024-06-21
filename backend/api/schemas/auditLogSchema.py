# schemas/auditLogSchema.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AuditLog(BaseModel):
    id: int
    user_id: Optional[int]  # Optional for failed logins
    action: str
    timestamp: datetime
    details: Optional[str]

    class Config:
        orm_mode = True
