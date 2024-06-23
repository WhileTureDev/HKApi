# controllers/k8sControllers/podController.py

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

router = APIRouter()
logger = logging.getLogger(__name__)

# Load Kubernetes configuration
config.load_incluster_config()

@router.get("/pods", response_model=dict)
async def list_pods(
    request: Request,
    namespace: str = Query(..., description="The namespace to list pods from"),
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

        core_v1 = client.CoreV1Api()
        pods = core_v1.list_namespaced_pod(namespace=namespace)
        pod_list = [{
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "node_name": pod.spec.node_name,
            "start_time": pod.status.start_time
        } for pod in pods.items]

        logger.info(f"User {current_user.username} successfully listed pods in namespace {namespace}")
        return {"pods": pod_list}

    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"Namespace {namespace} not found")
            raise HTTPException(status_code=404, detail=f"Namespace {namespace} not found")
        else:
            logger.error(f"Error listing pods in namespace {namespace}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"An error occurred while listing pods: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")

    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/pod", response_model=dict)
async def get_pod_details(
    request: Request,
    namespace: str = Query(..., description="The namespace of the pod"),
    pod_name: str = Query(..., description="The name of the pod"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/pod"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is fetching details for pod {pod_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)

        pod_details = {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "node_name": pod.spec.node_name,
            "start_time": pod.status.start_time,
            "containers": [
                {
                    "name": container.name,
                    "image": container.image,
                    "ready": status.ready,
                    "restart_count": status.restart_count
                } for container, status in zip(pod.spec.containers, pod.status.container_statuses)
            ],
            "host_ip": pod.status.host_ip,
            "pod_ip": pod.status.pod_ip
        }

        logger.info(f"User {current_user.username} successfully fetched details for pod {pod_name} in namespace {namespace}")
        return pod_details

    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"Pod {pod_name} not found in namespace {namespace}")
            raise HTTPException(status_code=404, detail=f"Pod {pod_name} not found in namespace {namespace}")
        else:
            logger.error(f"Error reading pod {pod_name} in namespace {namespace}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"An error occurred while fetching pod details: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")

    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
