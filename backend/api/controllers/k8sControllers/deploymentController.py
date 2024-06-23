# controllers/k8sControllers/deploymentController.py

import logging
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from kubernetes import client, config
from sqlalchemy.orm import Session

from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)
from models.userModel import User as UserModel
from utils.auth import get_current_active_user
from utils.database import get_db
from utils.security import get_current_user_roles, is_admin, check_project_and_namespace_ownership

router = APIRouter()
logger = logging.getLogger(__name__)

# Load Kubernetes configuration
config.load_incluster_config()

@router.get("/deployments", response_model=dict)
async def list_deployments(
    namespace: str = Query(..., description="The namespace to list deployments from"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/deployments"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is listing deployments in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        apps_v1 = client.AppsV1Api()
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
        deployment_list = [{
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "replicas": deployment.spec.replicas,
            "available_replicas": deployment.status.available_replicas,
            "unavailable_replicas": deployment.status.unavailable_replicas,
            "updated_replicas": deployment.status.updated_replicas
        } for deployment in deployments.items]

        logger.info(f"User {current_user.username} successfully listed deployments in namespace {namespace}")
        return {"deployments": deployment_list}

    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"Namespace {namespace} not found")
            raise HTTPException(status_code=404, detail=f"Namespace {namespace} not found")
        else:
            logger.error(f"Error listing deployments in namespace {namespace}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"An error occurred while listing deployments: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")

    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/deployment", response_model=dict)
async def get_deployment_details(
    namespace: str = Query(..., description="The namespace of the deployment"),
    deployment_name: str = Query(..., description="The name of the deployment"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/deployment"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is fetching details for deployment {deployment_name} in namespace "
                    f"{namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        apps_v1 = client.AppsV1Api()
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        deployment_details = {
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "replicas": deployment.spec.replicas,
            "available_replicas": deployment.status.available_replicas,
            "unavailable_replicas": deployment.status.unavailable_replicas,
            "updated_replicas": deployment.status.updated_replicas,
            "strategy": deployment.spec.strategy.type,
            "conditions": [
                {
                    "type": condition.type,
                    "status": condition.status,
                    "last_update_time": condition.last_update_time,
                    "last_transition_time": condition.last_transition_time,
                    "reason": condition.reason,
                    "message": condition.message
                } for condition in deployment.status.conditions or []
            ]
        }

        logger.info(f"User {current_user.username} successfully fetched details for deployment {deployment_name} in "
                    f"namespace {namespace}")
        return deployment_details

    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"Deployment {deployment_name} not found in namespace {namespace}")
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_name} not found in namespace "
                                                        f"{namespace}")
        else:
            logger.error(f"Error reading deployment {deployment_name} in namespace {namespace}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"An error occurred while fetching deployment details: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")

    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
