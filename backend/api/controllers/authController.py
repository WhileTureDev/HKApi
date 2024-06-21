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
from utils.change_logger import log_change  # Import the change logger

router = APIRouter()
logger = logging.getLogger(__name__)

access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

@router.post("/token", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info(f"Attempting login for user: {form_data.username}")
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            log_change(db, user_id=None, action="failed_login", resource="user", resource_id=None, resource_name=form_data.username, project_name=None, details=f"Failed login attempt for username: {form_data.username}")
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
        log_change(db, user.id, action="successful_login", resource="user", resource_id=user.id, resource_name=user.username, project_name=None, details=f"Successful login for username: {form_data.username}")
        logger.info(f"Login successful for user: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
