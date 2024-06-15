from fastapi import APIRouter
from controllers import helmController

router = APIRouter()
router.include_router(helmController.router, tags=["helm"])
