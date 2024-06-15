from fastapi import FastAPI
from models import Base
from utils.database import create_database_if_not_exists, create_tables, get_db
from controllers import authController, projectController, helmController, helmRepositoryController, userController
from utils.helm import configure_helm_repositories_from_db

app = FastAPI()

# Create the database if it doesn't exist
create_database_if_not_exists()

# Ensure this runs only once and in a single-threaded context
create_tables()


# Configure Helm repositories from the database
def startup_event():
    db_session = next(get_db())
    configure_helm_repositories_from_db(db_session)
    db_session.close()


app.add_event_handler("startup", startup_event)

# Include routes with tags
app.include_router(userController.router, tags=["Users"])
app.include_router(projectController.router, tags=["Projects"])
app.include_router(authController.router, tags=["Auth"])
app.include_router(helmController.router, tags=["Helm"])
app.include_router(helmRepositoryController.router, tags=["Helm Repositories"])


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Hello World"}
