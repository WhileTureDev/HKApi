# controllers/authController.py

import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from utils.database import get_db
from utils.shared_utils import create_access_token
from utils.auth import authenticate_user
from schemas.tokenSchema import Token
from utils.change_logger import log_audit

router = APIRouter()
logger = logging.getLogger(__name__)

access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

@router.post("/token", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Attempting login for user: {form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        log_audit(db, action="failed_login", details=f"Failed login attempt for username: {form_data.username}")
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    log_audit(db, user_id=user.id, action="successful_login", details=f"Successful login for username: {form_data.username}")
    logger.info(f"Login successful for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}
