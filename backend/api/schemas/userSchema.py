from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: EmailStr
    disabled: Optional[bool] = False


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserInDB(UserBase):
    hashed_password: str
