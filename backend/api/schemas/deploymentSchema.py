from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional

class DeploymentBase(BaseModel):
    project: str
    chart_name: str
    chart_repo_url: str
    namespace_name: str
    values: Dict[str, Any]

class DeploymentCreate(DeploymentBase):
    pass

class Deployment(DeploymentBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    status: str  # Add status field

    class Config:
        orm_mode = True
