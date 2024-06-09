from pydantic import BaseModel
from fastapi import Form


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class User(BaseModel):
    username: str = Form(...)
    full_name: str = Form(...)
    email: str = Form(...)


class UserCreate(User):
    password: str

    class Config:
        validate_assignment = True


class UserInDB(User):
    password: str


class ReleaseInfo(BaseModel):
    name: str
    namespace: str
    chart_name: str
    chart_repo_url: str
    release_name: str
    provider: str
