# controllers/k8sControllers/configMapController.py

import logging
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from kubernetes import client, config
from sqlalchemy.orm import Session

from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)
from models.userModel import User as UserModel
from utils.auth import get_current_active_user
from utils.database import get_db
from utils.security import get_current_user_roles, is_admin, check_project_and_namespace_ownership
from utils.error_handling import handle_k8s_exception, handle_general_exception

router = APIRouter()
logger = logging.getLogger(__name__)

# Load Kubernetes configuration
config.load_incluster_config()

@router.get("/configmaps", response_model=dict)
async def list_configmaps(
    request: Request,
    namespace: str = Query(..., description="The namespace to list ConfigMaps from"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/configmaps"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is listing ConfigMaps in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        configmaps = core_v1.list_namespaced_config_map(namespace=namespace)
        configmap_list = [{
            "name": configmap.metadata.name,
            "namespace": configmap.metadata.namespace,
            "data": configmap.data,
            "created_at": configmap.metadata.creation_timestamp
        } for configmap in configmaps.items]

        logger.info(f"User {current_user.username} successfully listed ConfigMaps in namespace {namespace}")
        return {"configmaps": configmap_list}

    except client.exceptions.ApiException as e:
        handle_k8s_exception(e)

    except Exception as e:
        handle_general_exception(e)

    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
