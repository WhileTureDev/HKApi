from pydantic import BaseModel
from datetime import datetime

class HelmRepositoryCreate(BaseModel):
    name: str
    url: str

class HelmRepository(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
