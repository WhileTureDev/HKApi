from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models.deploymentModel import Deployment as DeploymentModel
from schemas.deploymentSchema import Deployment as DeploymentSchema
from utils.database import get_db

router = APIRouter()


@router.get("/deployments/", response_model=List[DeploymentSchema])
def list_deployments(db: Session = Depends(get_db)):
    deployments = db.query(DeploymentModel).all()
    if not deployments:
        raise HTTPException(status_code=404, detail="No deployments found")
    return deployments
