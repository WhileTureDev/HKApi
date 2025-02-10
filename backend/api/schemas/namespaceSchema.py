# schemas/namespaceSchema.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class NamespaceBase(BaseModel):
    name: str = Field(..., description="Unique name of the namespace")
    project_id: Optional[int] = Field(None, description="ID of the associated project")

class NamespaceCreate(NamespaceBase):
    pass

class Namespace(NamespaceBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
