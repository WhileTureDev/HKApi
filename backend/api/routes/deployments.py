from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..utils.database import get_db
from ..utils.k8s import get_deployment_status
from ..schemas.deploymentSchema import DeploymentStatus

router = APIRouter()


@router.get("/deployments/{namespace}/{name}/status", response_model=DeploymentStatus)
def get_status(namespace: str, name: str, db: Session = Depends(get_db)):
    status = get_deployment_status(namespace, name)
    if not status:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return status
