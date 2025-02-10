# controllers/authControllers/authController.py

import os
import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from utils.database import get_db
from utils.shared_utils import create_access_token
from utils.auth import authenticate_user
from schemas.tokenSchema import Token
from utils.circuit_breaker import call_database_operation
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)

router = APIRouter()
logger = logging.getLogger(__name__)

access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


@router.post("/token", response_model=Token)
def login_for_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    start_time = time.time()
    logger.info(f"Received authentication request: Method={request.method}, URL={request.url}, Headers={dict(request.headers)}")
    method = request.method
    endpoint = "/api/v1/auth/token"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Attempting login for user: {form_data.username}")
        user = call_database_operation(authenticate_user, db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Login failed for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        logger.info(f"Login successful for user: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
