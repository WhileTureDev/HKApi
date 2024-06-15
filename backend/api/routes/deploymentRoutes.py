from fastapi import APIRouter
from controllers import deploymentController

router = APIRouter()
router.include_router(deploymentController.router, tags=["deployments"])
