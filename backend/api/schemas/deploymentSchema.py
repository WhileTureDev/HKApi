from pydantic import BaseModel
from datetime import datetime


class DeploymentBase(BaseModel):
    release_type: str
    install_type: str
    chart_name: str
    chart_repo_url: str
    namespace_id: int


class DeploymentCreate(DeploymentBase):
    pass


class Deployment(DeploymentBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
