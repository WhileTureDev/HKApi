from fastapi import APIRouter
from ..controllers import userController

router = APIRouter()
router.include_router(userController.router, tags=["users"])
