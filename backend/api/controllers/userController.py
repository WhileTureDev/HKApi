import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from models.userModel import User as UserModel
from schemas.userSchema import UserCreate, User as UserSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from utils.security import get_password_hash

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/users/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to create a new user: {user.email}")
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        logger.warning(f"Email {user.email} already registered")
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = UserModel(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_password,
        disabled=user.disabled,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User {user.email} created successfully")
    return new_user

@router.get("/users/me", response_model=UserSchema)
def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    logger.info(f"Fetching details for user {current_user.username}")
    return current_user
