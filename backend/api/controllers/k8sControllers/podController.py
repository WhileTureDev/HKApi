# controllers/k8sControllers/podController.py

import logging
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
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

@router.get("/", response_model=dict)
async def list_pods(
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

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return {"pods": pod_list}

    except Exception as e:
        logger.error(f"Error listing pods: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail=f"Error listing pods: {str(e)}")
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/{pod_name}", response_model=dict)
async def get_pod_details(
    namespace: str = Query(..., description="The namespace of the pod"),
    pod_name: str = Path(..., description="The name of the pod"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/pods/{pod_name}"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is retrieving details for pod {pod_name}")

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
            "containers": [{"name": container.name, "image": container.image} for container in pod.spec.containers],
            "host_ip": pod.status.host_ip,
            "pod_ip": pod.status.pod_ip
        }

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return {"pod": pod_details}

    except client.exceptions.ApiException as e:
        logger.error(f"Error retrieving pod details: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=e.status, detail=f"Error retrieving pod: {str(e)}")
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.post("/", response_model=dict)
async def create_pod(
    namespace: str,
    pod_name: str,
    image: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "POST"
    endpoint = "/pods"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is creating a pod in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to create pod in this namespace")

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

        created_pod = core_v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)

        # Log the change with resource_name and project_name, including additional details
        namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
        project_obj = db.query(ProjectModel).filter_by(id=namespace_obj.project_id).first()
        log_change(
            db,
            current_user.id,
            action="create",
            resource="pod",
            resource_id=created_pod.metadata.uid,  # Use created_pod.metadata.uid as resource_id
            resource_name=pod_name,
            project_name=project_obj.name if project_obj else "N/A",
            details=f"Pod {pod_name} created in namespace {namespace}"
        )

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return {"pod": {"name": created_pod.metadata.name, "status": "Created"}}

    except client.exceptions.ApiException as e:
        logger.error(f"Error creating pod: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=e.status, detail=f"Error creating pod: {str(e)}")
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.put("/{pod_name}", response_model=dict)
async def update_pod(
    namespace: str,
    pod_name: str,
    image: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "PUT"
    endpoint = "/pods/{pod_name}"
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

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return {"pod": updated_pod_details}

    except client.exceptions.ApiException as e:
        logger.error(f"Error updating pod: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=e.status, detail=f"Error updating pod: {str(e)}")
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.delete("/{pod_name}", response_model=dict)
async def delete_pod(
    namespace: str,
    pod_name: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "DELETE"
    endpoint = "/pods/{pod_name}"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is deleting pod {pod_name}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to delete pod in this namespace")

        core_v1 = client.CoreV1Api()
        # Delete the pod
        core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)

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

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return {"status": "Deleted", "pod_name": pod_name}

    except client.exceptions.ApiException as e:
        logger.error(f"Error deleting pod: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=e.status, detail=f"Error deleting pod: {str(e)}")
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/{pod_name}/logs", response_model=dict)
async def get_pod_logs(
    namespace: str,
    pod_name: str,
    container: Optional[str] = Query(None, description="The name of the container (optional)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/pods/{pod_name}/logs"
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

        logger.info(f"User {current_user.username} successfully fetched logs for pod {pod_name} "
                    f"in namespace {namespace}")

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return {"logs": logs}

    except client.exceptions.ApiException as e:
        logger.error(f"Error fetching logs for pod: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=e.status, detail=f"Error fetching logs for pod: {str(e)}")
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()
