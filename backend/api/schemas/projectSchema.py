from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class UserBase(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    owner: Optional[UserBase] = None

    class Config:
        from_attributes = True  # This replaces orm_mode in newer versions
