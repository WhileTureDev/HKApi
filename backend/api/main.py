# main.py

import logging
import logging.config
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from controllers import authController, projectController, helmController, helmRepositoryController, userController, changeLogController
from controllers.adminControllers import adminHelmController, auditLogController  # Import the new audit log controller
from utils.database import create_database_if_not_exists, create_tables, get_db
from utils.logging_config import LOGGING_CONFIG
from utils.exception_handlers import ExceptionMiddleware
from models.userModel import User
from models.roleModel import Role
from models.userRoleModel import UserRole
from utils.shared_utils import get_password_hash
from sqlalchemy.orm import Session
import os

app = FastAPI()

# Initialize logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# Middleware to log requests
class LogRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response


# Add middleware for logging and exception handling
app.add_middleware(LogRequestsMiddleware)
app.add_middleware(ExceptionMiddleware)

# Create the database if it doesn't exist
create_database_if_not_exists()

# Ensure this runs only once and in a single-threaded context
create_tables()


def create_initial_admin(db: Session):
    admin_username = "admin"
    admin_email = "admin@example.com"
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")

    admin_user = db.query(User).filter(User.username == admin_username).first()
    if not admin_user:
        admin_user = User(
            username=admin_username,
            full_name="Administrator",
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            disabled=False
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)

        user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
        db.add(user_role)
        db.commit()


# Initialize the database session and create the initial admin
with next(get_db()) as db:
    create_initial_admin(db)

# Include routes
app.include_router(userController.router, tags=["users"])
app.include_router(authController.router, tags=["auth"])
app.include_router(projectController.router, tags=["projects"])
app.include_router(helmController.router, tags=["helm"])
app.include_router(helmRepositoryController.router, tags=["repositories"])
app.include_router(changeLogController.router, tags=["changelogs"])
app.include_router(adminHelmController.router, tags=["admin"])
app.include_router(auditLogController.router, tags=["audit_logs"])  # Include the new router


@app.get("/")
def read_root():
    return {"message": "Hello World"}
