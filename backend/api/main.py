from fastapi import FastAPI
from .models import Base
from .utils.database import engine
from .routes import userRoutes, projectRoutes
from .controllers import authController

app = FastAPI()

# Create the database tables
Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(userRoutes.router)
app.include_router(projectRoutes.router)
app.include_router(authController.router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
