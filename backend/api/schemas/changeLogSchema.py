# schemas/changeLogSchema.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChangeLog(BaseModel):
    id: int
    user_id: int
    user_name: str
    action: str
    resource: str
    resource_id: int
    resource_name: str
    project_name: Optional[str]
    timestamp: datetime
    details: Optional[str]

    class Config:
        orm_mode = True
