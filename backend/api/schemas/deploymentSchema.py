from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Union

class DeploymentCreate(BaseModel):
    release_name: str
    chart_name: str
    chart_repo_url: str
    namespace: str
    project: str
    values: Dict[str, Union[str, int, float, bool, None]]
    version: Optional[str] = None
    debug: Optional[bool] = False

    class Config:
        orm_mode = True


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


class RollbackOptions(BaseModel):
    force: Optional[bool] = False
    recreate_pods: Optional[bool] = False
