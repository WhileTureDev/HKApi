import yaml
from fastapi import APIRouter, HTTPException, UploadFile
from kubernetes import client
from kubernetes.client import ApiException, V1Namespace

from .db import get_deployments_db

router = APIRouter()


# Read all deployments from database
@router.get("/api/v1/list-db-deployments")
def get_deployments_from_database_api():
    deployments = get_deployments_db()
    if not deployments:
        raise HTTPException(status_code=204, detail="No namespaces found.")
    return deployments
