# controllers/k8sControllers/configMapController.py

import json
import logging
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Form, status, Request
from kubernetes import client, config
from kubernetes.client import ApiException
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
        logger.info(f"User {current_user.email} is listing ConfigMaps in namespace {namespace}")

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

        logger.info(f"User {current_user.email} successfully listed ConfigMaps in namespace {namespace}")
        return {"configmaps": configmap_list}

    except client.exceptions.ApiException as e:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        handle_k8s_exception(e)

    except Exception as e:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        handle_general_exception(e)

    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/configmap", response_model=dict)
async def get_configmap_details(
    namespace: str = Query(..., description="The namespace of the ConfigMap"),
    configmap_name: str = Query(..., description="The name of the ConfigMap"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/configmap"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.email} is fetching details for ConfigMap {configmap_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        configmap = core_v1.read_namespaced_config_map(name=configmap_name, namespace=namespace)

        configmap_details = {
            "name": configmap.metadata.name,
            "namespace": configmap.metadata.namespace,
            "data": configmap.data,
            "created_at": configmap.metadata.creation_timestamp
        }

        logger.info(f"User {current_user.email} successfully fetched details for ConfigMap {configmap_name} in namespace {namespace}")
        return configmap_details

    except client.exceptions.ApiException as e:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        if e.status == 404:
            logger.error(f"ConfigMap {configmap_name} not found in namespace {namespace}")
            raise HTTPException(status_code=404, detail=f"ConfigMap {configmap_name} not found in namespace {namespace}")
        else:
            handle_k8s_exception(e)

    except Exception as e:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        handle_general_exception(e)

    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.post("/configmap")
async def create_configmap(
    namespace: str = Form(..., description="The namespace to create the ConfigMap in"),
    configmap_name: str = Form(..., description="The name of the ConfigMap"),
    data: str = Form(..., description="The data for the ConfigMap in JSON format"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "POST"
    endpoint = "/configmap"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.email} is creating a ConfigMap {configmap_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        configmap_data = json.loads(data)

        configmap_body = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(name=configmap_name),
            data=configmap_data
        )

        configmap = core_v1.create_namespaced_config_map(namespace=namespace, body=configmap_body)
        logger.info(f"User {current_user.email} successfully created ConfigMap {configmap_name} in namespace {namespace}")

        return {
            "name": configmap.metadata.name,
            "namespace": configmap.metadata.namespace,
            "data": configmap.data,
            "created_at": configmap.metadata.creation_timestamp
        }
    except client.exceptions.ApiException as e:
        handle_k8s_exception(e)
    except Exception as e:
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.put("/configmap")
async def update_configmap(
    namespace: str = Form(..., description="The namespace of the ConfigMap"),
    configmap_name: str = Form(..., description="The name of the ConfigMap"),
    data: str = Form(..., description="The new data for the ConfigMap in JSON format"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "PUT"
    endpoint = "/configmap"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.email} is updating ConfigMap {configmap_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        configmap_data = json.loads(data)

        # Fetch existing ConfigMap
        existing_configmap = core_v1.read_namespaced_config_map(name=configmap_name, namespace=namespace)

        # Update data
        existing_configmap.data = configmap_data

        # Update the ConfigMap
        updated_configmap = core_v1.patch_namespaced_config_map(name=configmap_name, namespace=namespace, body=existing_configmap)
        logger.info(f"User {current_user.email} successfully updated ConfigMap {configmap_name} in namespace {namespace}")

        return {
            "name": updated_configmap.metadata.name,
            "namespace": updated_configmap.metadata.namespace,
            "data": updated_configmap.data,
            "updated_at": updated_configmap.metadata.creation_timestamp
        }
    except ApiException as e:
        handle_k8s_exception(e)
    except Exception as e:
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.delete("/configmap", response_model=dict)
async def delete_configmap(
    request: Request,
    namespace: str = Query(..., description="The namespace of the ConfigMap"),
    name: str = Query(..., description="The name of the ConfigMap"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.email} is deleting ConfigMap {name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        core_v1 = client.CoreV1Api()
        core_v1.delete_namespaced_config_map(name=name, namespace=namespace)

        logger.info(f"User {current_user.email} successfully deleted ConfigMap {name} in namespace {namespace}")
        return {"message": f"ConfigMap {name} deleted successfully"}
    except client.exceptions.ApiException as e:
        handle_k8s_exception(e)
    except Exception as e:
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()