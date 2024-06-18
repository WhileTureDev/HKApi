from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.projectModel import Project as ProjectModel
from models.namespaceModel import Namespace as NamespaceModel
from models.userModel import User as UserModel

# to get a string like this run: openssl rand -hex 32
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except JWTError:
        return None
    return token_data


def check_project_and_namespace_ownership(db: Session, project: Optional[str], namespace: str, current_user: UserModel):
    project_obj = None

    # Check if the project exists and belongs to the current user if project is provided
    if project:
        project_obj = db.query(ProjectModel).filter_by(name=project, owner_id=current_user.id).first()
        if not project_obj:
            raise HTTPException(status_code=404, detail="Project not found")

    # Check if the namespace exists under any user
    namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
    if namespace_obj and namespace_obj.owner_id != current_user.id:
        # If the namespace exists and does not belong to the current user, raise an exception
        raise HTTPException(status_code=400, detail=f'User {current_user.username} does not own the namespace {namespace}')

    return project_obj, namespace_obj
