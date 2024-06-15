from pydantic import BaseModel
from typing import Optional, Dict
from  datetime import datetime

class DeploymentCreate(BaseModel):
    project: str
    chart_name: str
    chart_repo_url: str
    namespace_name: str
    release_name: str  # Add this line
    values: Dict

class Deployment(BaseModel):
    id: int
    project: str
    chart_name: str
    chart_repo_url: str
    namespace_name: str
    release_name: str  # Add this line
    values: Dict
    revision: int
    install_type: str
    active: bool
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
