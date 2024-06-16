import logging
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from controllers import authController, projectController, helmController, helmRepositoryController, userController
from utils.database import create_database_if_not_exists, create_tables
from utils.logging_config import LOGGING_CONFIG
from utils.exception_handlers import ExceptionMiddleware

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

# Include routes
app.include_router(userController.router, tags=["users"])
app.include_router(authController.router, tags=["auth"])
app.include_router(projectController.router, tags=["projects"])
app.include_router(helmController.router, tags=["helm"])
app.include_router(helmRepositoryController.router, tags=["repositories"])

@app.get("/")
def read_root():
    return {"message": "Hello World"}
