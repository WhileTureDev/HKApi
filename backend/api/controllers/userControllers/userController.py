# controllers/userControllers/userController.py

import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from models.userModel import User as UserModel
from models.roleModel import Role as RoleModel
from models.userRoleModel import UserRole as UserRoleModel
from schemas.userSchema import UserCreate, User as UserSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from utils.shared_utils import get_password_hash
from utils.change_logger import log_change
from utils.security import get_current_user_roles, is_admin
from utils.circuit_breaker import call_database_operation
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/users", response_model=UserSchema)
def create_user(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Attempting to create a new user: {user.email}")
        db_user = call_database_operation(lambda: db.query(UserModel).filter(UserModel.email == user.email).first())
        if db_user:
            logger.warning(f"Email {user.email} already registered")
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = UserModel(
            email=user.email,
            full_name=user.full_name,
            hashed_password=get_password_hash(user.password),
            disabled=user.disabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        call_database_operation(lambda: db.add(new_user))
        call_database_operation(lambda: db.commit())
        call_database_operation(lambda: db.refresh(new_user))
        logger.info(f"User {user.email} created successfully")
        # Log the change
        log_change(db, new_user.id, action="create", resource="user", resource_id=new_user.id,
                   resource_name=user.email, project_name="N/A", details=f"User {user.email} created")
        return new_user
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while creating user: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/users/me", response_model=UserSchema)
def read_users_me(request: Request, current_user: UserModel = Depends(get_current_active_user)):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Fetching details for user {current_user.email}")
        return current_user
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while fetching user details: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.post("/users/{user_id}/roles/{role_id}")
async def assign_role_to_user(user_id: int, role_id: int, request: Request, db: Session = Depends(get_db),
                              current_user: UserModel = Depends(get_current_active_user),
                              current_user_roles: List[str] = Depends(get_current_user_roles)):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    if not is_admin(current_user_roles):
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        user = call_database_operation(lambda: db.query(UserModel).filter(UserModel.id == user_id).first())
        role = call_database_operation(lambda: db.query(RoleModel).filter(RoleModel.id == role_id).first())

        if not user or not role:
            ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
            raise HTTPException(status_code=404, detail="User or role not found")

        user_role = UserRoleModel(user_id=user_id, role_id=role_id)
        call_database_operation(lambda: db.add(user_role))
        call_database_operation(lambda: db.commit())
        logger.info(f"Assigned role {role.name} to user {user.email}")
        log_change(db, current_user.id, action="assign_role", resource="user_role", resource_id=user_role.id,
                   resource_name=user.email, project_name="N/A",
                   details=f"Assigned role {role.name} to user {user.email}")

        return {"message": "Role assigned successfully"}
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while assigning the role: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
