from pydantic import BaseModel
from datetime import datetime

class HelmRepositoryBase(BaseModel):
    name: str
    url: str

class HelmRepositoryCreate(HelmRepositoryBase):
    pass

class HelmRepository(HelmRepositoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # Ensure this is set
