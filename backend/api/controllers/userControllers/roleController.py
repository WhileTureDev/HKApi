# controllers/roleControllers/roleController.py

import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models.roleModel import Role
from models.userRoleModel import UserRole
from models.userModel import User
from utils.database import get_db
from utils.auth import get_current_active_user
from utils.circuit_breaker import call_database_operation
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/roles", response_model=dict)
def create_role(
    request: Request,
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        role = call_database_operation(lambda: db.query(Role).filter_by(name=name).first())
        if role:
            logger.warning(f"Role with name {name} already exists")
            raise HTTPException(status_code=400, detail="Role already exists")

        new_role = Role(name=name)
        call_database_operation(lambda: db.add(new_role))
        call_database_operation(lambda: db.commit())
        call_database_operation(lambda: db.refresh(new_role))
        logger.info(f"Role {name} created successfully")
        return {"message": "Role created successfully", "role": new_role.name}
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while creating the role: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.post("/roles/assign", response_model=dict)
def assign_role(
    request: Request,
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        user = call_database_operation(lambda: db.query(User).filter_by(id=user_id).first())
        if not user:
            logger.warning(f"User with ID {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        role = call_database_operation(lambda: db.query(Role).filter_by(name=role_name).first())
        if not role:
            logger.warning(f"Role with name {role_name} not found")
            raise HTTPException(status_code=404, detail="Role not found")

        user_role = call_database_operation(lambda: db.query(UserRole).filter_by(user_id=user_id, role_id=role.id).first())
        if user_role:
            logger.warning(f"User with ID {user_id} already has the role {role_name}")
            raise HTTPException(status_code=400, detail="User already has this role")

        new_user_role = UserRole(user_id=user_id, role_id=role.id)
        call_database_operation(lambda: db.add(new_user_role))
        call_database_operation(lambda: db.commit())
        logger.info(f"Role {role_name} assigned to user ID {user_id} successfully")
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
