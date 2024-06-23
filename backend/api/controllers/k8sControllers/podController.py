# controllers/k8sControllers/podController.py

import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from kubernetes import client, config
from typing import List
from models.namespaceModel import Namespace as NamespaceModel
from models.userModel import User as UserModel
from utils.database import get_db
from utils.auth import get_current_active_user
from utils.security import get_current_user_roles, is_admin, check_project_and_namespace_ownership
from utils.circuit_breaker import call_database_operation
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Load Kubernetes configuration
config.load_incluster_config()


@router.get("/pods", response_model=List[dict])
async def list_pods(
        request: Request,
        namespace: str,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/pods"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is listing pods in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        v1 = client.CoreV1Api()

        # Check if the namespace exists
        try:
            v1.read_namespace(namespace)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                logger.error(f"Namespace {namespace} not found")
                raise HTTPException(status_code=404, detail=f"Namespace {namespace} not found")
            else:
                logger.error(f"Error reading namespace {namespace}: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")

        pods = v1.list_namespaced_pod(namespace)
        pod_list = [{"name": pod.metadata.name, "status": pod.status.phase} for pod in pods.items]

        logger.info(f"User {current_user.username} successfully listed pods in namespace {namespace}")
        return pod_list
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while listing pods: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
