from fastapi import FastAPI
from models import Base
from utils.database import create_database_if_not_exists, create_tables
from routes import userRoutes, projectRoutes, deploymentRoutes  # Import deploymentRoutes
from controllers import authController

app = FastAPI()

# Create the database if it doesn't exist
create_database_if_not_exists()

# Ensure this runs only once and in a single-threaded context
create_tables()

# Include routes
app.include_router(userRoutes.router)
app.include_router(projectRoutes.router)
app.include_router(deploymentRoutes.router)  # Include deploymentRoutes
app.include_router(authController.router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
