from fastapi import FastAPI
from kubernetes import config
from utils.helm import load_k8s_config
from models import Base
from utils.database import create_database_if_not_exists, create_tables
from routes import userRoutes, projectRoutes, deploymentRoutes, helmRoutes
from controllers import authController

# Load Kubernetes configuration
load_k8s_config()

app = FastAPI()

# Create the database if it doesn't exist
create_database_if_not_exists()

# Ensure this runs only once and in a single-threaded context
create_tables()

# Include routes
app.include_router(userRoutes.router)
app.include_router(projectRoutes.router)
app.include_router(deploymentRoutes.router)
app.include_router(helmRoutes.router)
app.include_router(authController.router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}
