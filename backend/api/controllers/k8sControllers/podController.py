# controllers/k8sControllers/podController.py

import logging
import time
from typing import List, Optional

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
from utils.change_logger import log_change
from models.namespaceModel import Namespace as NamespaceModel
from models.projectModel import Project as ProjectModel

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
            "start_time": pod.status.start_time,
            "containers": [{"name": container.name, "image": container.image} for container in pod.spec.containers],
            "host_ip": pod.status.host_ip,
            "pod_ip": pod.status.pod_ip
        } for pod in pods.items]

        # Remove keys with null values for each pod
        pod_list = [{k: v for k, v in pod.items() if v is not None} for pod in pod_list]

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
                    "ready": status.ready if pod.status.container_statuses else False,
                    "restart_count": status.restart_count if pod.status.container_statuses else 0
                } for container, status in zip(pod.spec.containers, pod.status.container_statuses or [])
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

@router.post("/pod")
async def create_pod(
    request: Request,
    namespace: str,
    pod_name: str,
    image: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "POST"
    endpoint = "/pod"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is creating pod {pod_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod_name},
            "spec": {
                "containers": [
                    {
                        "name": pod_name,
                        "image": image,
                        "ports": [{"containerPort": 80}]
                    }
                ]
            }
        }

        pod = core_v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        logger.info(f"User {current_user.username} successfully created pod {pod_name} in namespace {namespace}")

        # Log the change with resource_name and project_name, including additional details
        namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
        project_obj = db.query(ProjectModel).filter_by(id=namespace_obj.project_id).first()
        log_change(
            db,
            current_user.id,
            action="create",
            resource="pod",
            resource_id=pod.metadata.uid,  # Use pod.metadata.uid as resource_id
            resource_name=pod_name,
            project_name=project_obj.name if project_obj else "N/A",
            details=f"Pod {pod_name} created in namespace {namespace}"
        )

        pod_details = {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "node_name": pod.spec.node_name,
            "start_time": pod.status.start_time,
            "containers": [{"name": container.name, "image": container.image} for container in pod.spec.containers],
            "host_ip": pod.status.host_ip,
            "pod_ip": pod.status.pod_ip
        }

        # Remove keys with null values
        pod_details = {k: v for k, v in pod_details.items() if v is not None}

        return pod_details
    except client.exceptions.ApiException as e:
        if e.status == 409:
            logger.error(f"Pod {pod_name} already exists in namespace {namespace}: {e}")
            raise HTTPException(status_code=409, detail=f"Pod {pod_name} already exists in namespace {namespace}")
        elif e.status == 404:
            logger.error(f"Namespace {namespace} not found")
            raise HTTPException(status_code=404, detail=f"Namespace {namespace} not found")
        else:
            logger.error(f"Error creating pod {pod_name} in namespace {namespace}: {e}")
            raise HTTPException(status_code=e.status, detail=e.body)
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while creating the pod: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.put("/pod")
async def update_pod(
    request: Request,
    namespace: str,
    pod_name: str,
    image: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "PUT"
    endpoint = "/pod"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is updating pod {pod_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)

        # Update the pod's container image
        pod.spec.containers[0].image = image

        updated_pod = core_v1.replace_namespaced_pod(name=pod_name, namespace=namespace, body=pod)
        logger.info(f"User {current_user.username} successfully updated pod {pod_name} in namespace {namespace}")

        # Log the change with resource_name and project_name, including additional details
        namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
        project_obj = db.query(ProjectModel).filter_by(id=namespace_obj.project_id).first()
        log_change(
            db,
            current_user.id,
            action="update",
            resource="pod",
            resource_id=updated_pod.metadata.uid,  # Use updated_pod.metadata.uid as resource_id
            resource_name=pod_name,
            project_name=project_obj.name if project_obj else "N/A",
            details=f"Pod {pod_name} updated in namespace {namespace} with new image {image}"
        )

        updated_pod_details = {
            "name": updated_pod.metadata.name,
            "namespace": updated_pod.metadata.namespace,
            "status": updated_pod.status.phase,
            "node_name": updated_pod.spec.node_name,
            "start_time": updated_pod.status.start_time,
            "containers": [{"name": container.name, "image": container.image} for container in updated_pod.spec.containers],
            "host_ip": updated_pod.status.host_ip,
            "pod_ip": updated_pod.status.pod_ip
        }

        # Remove keys with null values
        updated_pod_details = {k: v for k, v in updated_pod_details.items() if v is not None}

        return updated_pod_details
    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"Pod {pod_name} not found in namespace {namespace}: {e}")
            raise HTTPException(status_code=404, detail=f"Pod {pod_name} not found in namespace {namespace}")
        else:
            logger.error(f"Error updating pod {pod_name} in namespace {namespace}: {e}")
            raise HTTPException(status_code=e.status, detail=e.body)
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while updating the pod: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.delete("/pod")
async def delete_pod(
    request: Request,
    namespace: str,
    pod_name: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "DELETE"
    endpoint = "/pod"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is deleting pod {pod_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        logger.info(f"User {current_user.username} successfully deleted pod {pod_name} in namespace {namespace}")

        # Log the change with resource_name and project_name, including additional details
        namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
        project_obj = db.query(ProjectModel).filter_by(id=namespace_obj.project_id).first()
        log_change(
            db,
            current_user.id,
            action="delete",
            resource="pod",
            resource_id=pod_name,
            resource_name=pod_name,
            project_name=project_obj.name if project_obj else "N/A",
            details=f"Pod {pod_name} deleted in namespace {namespace}"
        )

        return {"message": f"Pod {pod_name} deleted successfully"}
    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"Pod {pod_name} not found in namespace {namespace}: {e}")
            raise HTTPException(status_code=404, detail=f"Pod {pod_name} not found in namespace {namespace}")
        else:
            logger.error(f"Error deleting pod {pod_name} in namespace {namespace}: {e}")
            raise HTTPException(status_code=e.status, detail=e.body)
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while deleting the pod: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/pod/logs", response_model=dict)
async def get_pod_logs(
    request: Request,
    namespace: str = Query(..., description="The namespace of the pod"),
    pod_name: str = Query(..., description="The name of the pod"),
    container: Optional[str] = Query(None, description="The name of the container (optional)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/pod/logs"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is fetching logs for pod {pod_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        if container:
            logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, container=container)
        else:
            logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace)

        logger.info(f"User {current_user.username} successfully fetched logs for pod {pod_name} in namespace {namespace}")

        return {"logs": logs}

    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"Pod {pod_name} not found in namespace {namespace}")
            raise HTTPException(status_code=404, detail=f"Pod {pod_name} not found in namespace {namespace}")
        else:
            logger.error(f"Error fetching logs for pod {pod_name} in namespace {namespace}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"An error occurred while fetching pod logs: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")

    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
