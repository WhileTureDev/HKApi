from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class User(BaseModel):
    username: str
    full_name: str
    email: str


class UserCreate(User):
    password: str


class UserInDB(User):
    password: str
