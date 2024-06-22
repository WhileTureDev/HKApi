# controllers/userController.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List  # Import the List type from typing
from models.userModel import User as UserModel
from models.roleModel import Role as RoleModel
from models.userRoleModel import UserRole as UserRoleModel
from schemas.userSchema import UserCreate, User as UserSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from utils.shared_utils import get_password_hash
from utils.change_logger import log_change  # Import the change logger
from utils.security import get_current_user_roles, is_admin  # Import role utilities
from utils.circuit_breaker import call_database_operation  # Import the circuit breaker

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/users/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Attempting to create a new user: {user.email}")
        db_user = call_database_operation(db.query(UserModel).filter(UserModel.email == user.email).first)
        if db_user:
            logger.warning(f"Email {user.email} already registered")
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = UserModel(
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            hashed_password=get_password_hash(user.password),
            disabled=user.disabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        call_database_operation(db.add, new_user)
        call_database_operation(db.commit)
        call_database_operation(db.refresh, new_user)
        logger.info(f"User {user.email} created successfully")
        # Log the change
        log_change(db, new_user.id, action="create", resource="user", resource_id=new_user.id, resource_name=user.username, project_name="N/A", details=f"User {user.username} created")
        return new_user
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="An internal error occurred")

@router.get("/users/me", response_model=UserSchema)
def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    logger.info(f"Fetching details for user {current_user.username}")
    return current_user

@router.post("/users/{user_id}/roles/{role_id}")
async def assign_role_to_user(user_id: int, role_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_active_user), current_user_roles: List[str] = Depends(get_current_user_roles)):
    if not is_admin(current_user_roles):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    user = call_database_operation(db.query(UserModel).filter(UserModel.id == user_id).first)
    role = call_database_operation(db.query(RoleModel).filter(RoleModel.id == role_id).first)

    if not user or not role:
        raise HTTPException(status_code=404, detail="User or role not found")

    user_role = UserRoleModel(user_id=user_id, role_id=role_id)
    call_database_operation(db.add, user_role)
    call_database_operation(db.commit)
    log_change(db, current_user.id, action="assign_role", resource="user_role", resource_id=user_role.id, resource_name=user.username, project_name="N/A", details=f"Assigned role {role.name} to user {user.username}")

    return {"message": "Role assigned successfully"}
