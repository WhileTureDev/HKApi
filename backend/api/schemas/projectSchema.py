from typing import Optional, List
from pydantic import BaseModel, validator, constr
from datetime import datetime
from schemas.namespaceSchema import Namespace as NamespaceSchema
import re

# Constants for Kubernetes naming conventions
KUBE_NAME_REGEX = re.compile(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$')
MAX_NAME_LENGTH = 40

class UserBase(BaseModel):
    id: int
    username: str
    email: str
    full_name: str

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: constr(min_length=1, max_length=MAX_NAME_LENGTH)
    description: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if not KUBE_NAME_REGEX.match(v):
            raise ValueError(
                'Project name must contain only lowercase letters, numbers, or hyphens, '
                'and must start and end with a letter or number'
            )
        return v

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
