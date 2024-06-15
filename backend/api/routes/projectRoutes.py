from fastapi import APIRouter
from controllers import projectController

router = APIRouter()
router.include_router(projectController.router, tags=["projects"])
