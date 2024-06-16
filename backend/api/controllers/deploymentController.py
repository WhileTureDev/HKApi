import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from models.deploymentModel import Deployment as DeploymentModel
from schemas.deploymentSchema import Deployment as DeploymentSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/deployments/", response_model=List[DeploymentSchema])
def list_deployments(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.username} is listing deployments")
    deployments = db.query(DeploymentModel).all()
    if not deployments:
        logger.warning("No deployments found")
        raise HTTPException(status_code=404, detail="No deployments found")
    logger.info(f"Found {len(deployments)} deployments")
    return deployments
