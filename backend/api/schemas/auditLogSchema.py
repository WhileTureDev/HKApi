from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AuditLog(BaseModel):
    id: int
    user_id: int
    user_name: str
    action: str
    resource: str = "user"
    resource_id: Optional[int]
    resource_name: str = "N/A"
    timestamp: datetime
    details: Optional[str]

    class Config:
        orm_mode = True
