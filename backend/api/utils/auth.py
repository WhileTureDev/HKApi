import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from utils.database import get_db
from models.userModel import User
from models.roleModel import Role
from models.userRoleModel import UserRole
from utils.shared_utils import verify_password, decode_access_token, check_token_expiration
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    expired_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # First check if token is expired
        is_expired, error = check_token_expiration(token)
        if is_expired:
            logging.warning(f"Token validation failed: {error}")
            raise expired_token_exception
            
        # If not expired, decode the token
        token_data = decode_access_token(token)
        if token_data is None:
            raise credentials_exception
            
        user = db.query(User).filter(User.email == token_data.email).first()
        if user is None:
            raise credentials_exception
            
        return user
        
    except JWTError as e:
        logging.error(f"JWT error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logging.error(f"Unexpected error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_user_roles(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> List[str]:
    roles = db.query(Role.name).join(UserRole).filter(UserRole.user_id == current_user.id).all()
    role_names = [role.name for role in roles]
    logging.info(f"Roles for user {current_user.email}: {role_names}")
    return role_names

def is_admin(user_roles: List[str]) -> bool:
    is_admin_role = "admin" in user_roles
    logging.info(f"Is admin: {is_admin_role}")
    return is_admin_role
