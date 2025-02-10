from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from schemas.namespaceSchema import Namespace as NamespaceSchema


class UserBase(BaseModel):
    id: int
    username: str
    email: str
    full_name: str

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
    namespaces: List[NamespaceSchema] = []

    class Config:
        from_attributes = True


class ProjectResponse(Project):
    message: Optional[str] = None


class ProjectDeleteResponse(BaseModel):
    message: str
    project_id: int
    owner: UserBase

    class Config:
        from_attributes = True
