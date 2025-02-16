import logging.config
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from controllers.logControllers import changeLogController
from controllers.helmControllers import helmRepositoryController, helmController
from controllers.userControllers import userController, projectController, authController, namespaceController
from controllers.adminControllers import adminHelmController, auditLogController
from utils.database import create_database_if_not_exists, create_tables, get_db
from utils.logging_config import LOGGING_CONFIG
from utils.exception_handlers import ExceptionMiddleware
from models.userModel import User
from models.roleModel import Role
from models.userRoleModel import UserRole
from utils.shared_utils import get_password_hash
from sqlalchemy.orm import Session
import os
from utils.limiter import limiter
from controllers.monitorControllers.healthCheckController import router as health_check_router
from controllers.monitorControllers.metricsController import router as metrics_router
from controllers.k8sControllers import podController
from controllers.k8sControllers import deploymentController
from controllers.k8sControllers import configMapController

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Local development frontend
        "http://localhost:8000",  # Django development server
        "https://hkapi.dailytoolset.com",  # Production frontend
        "http://hkapi.dailytoolset.com",   # HTTP version
        "https://localhost:3001",          # HTTPS local development
        "https://localhost:8000",          # HTTPS Django development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

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

def create_default_user_role(db: Session):
    user_role = db.query(Role).filter(Role.name == "user").first()
    if not user_role:
        new_role = Role(name="user")
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        logger.info("Default 'user' role created")
    else:
        logger.info("'user' role already exists")

def create_initial_admin(db: Session):
    from sqlalchemy.exc import IntegrityError
    
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")

    try:
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                fullname="Administrator",
                hashed_password=get_password_hash(admin_password),
                disabled=False
            )
            db.add(admin_user)
            db.commit()
            logger.info("Initial admin user created")
        else:
            logger.info("Admin user already exists")
            
        # Ensure admin has admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role and not db.query(UserRole).filter(
            UserRole.user_id == admin_user.id,
            UserRole.role_id == admin_role.id
        ).first():
            user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db.add(user_role)
            db.commit()
            logger.info("Admin role assigned to admin user")
        
    except IntegrityError:
        db.rollback()
        logger.info("Admin user already exists (caught duplicate)")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {str(e)}")

# Initialize the database session and create the initial admin and default user role
with next(get_db()) as db:
    create_default_user_role(db)
    create_initial_admin(db)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Include routes with consistent /api/v1/ prefix
app.include_router(userController.router, prefix="/api/v1", tags=["users"])
app.include_router(authController.router, prefix="/api/v1", tags=["auth"])
app.include_router(projectController.router, prefix="/api/v1", tags=["projects"])
app.include_router(namespaceController.router, prefix="/api/v1/namespaces", tags=["namespaces"])
app.include_router(helmController.router, prefix="/api/v1", tags=["helm"])
app.include_router(helmRepositoryController.router, prefix="/api/v1/helm/repositories", tags=["repositories"])
app.include_router(changeLogController.router, prefix="/api/v1", tags=["changelogs"])
app.include_router(adminHelmController.router, prefix="/api/v1", tags=["admin"])
app.include_router(auditLogController.router, prefix="/api/v1", tags=["auditlogs"])
app.include_router(health_check_router, prefix="/api/v1", tags=["health"])
app.include_router(metrics_router, prefix="/api/v1", tags=["metrics"])
app.include_router(podController.router, prefix="/api/v1", tags=["pods"])
app.include_router(deploymentController.router, prefix="/api/v1", tags=["deployments"])
app.include_router(configMapController.router, prefix="/api/v1", tags=["configmaps"])


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )
