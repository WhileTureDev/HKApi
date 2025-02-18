# controllers/k8sControllers/namespaceController.py

import logging
import time
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Path, Request, Body
from pydantic import BaseModel
from kubernetes import client, config

router = APIRouter()
logger = logging.getLogger(__name__)

# Load Kubernetes configuration
config.load_incluster_config()

# Global metrics
global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
REQUEST_COUNT = 0
REQUEST_LATENCY = 0
IN_PROGRESS = 0
ERROR_COUNT = 0

# Pydantic models for request validation
class NamespaceCreate(BaseModel):
    namespace: str
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None

class NamespaceUpdate(BaseModel):
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None

@router.get("/namespaces")
async def list_namespaces(request: Request):
    """
    List all namespaces in the cluster
    """
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info("Listing all namespaces")
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace()
        
        namespace_list = []
        for ns in namespaces.items:
            namespace_list.append({
                "name": ns.metadata.name,
                "status": ns.status.phase,
                "creation_time": ns.metadata.creation_timestamp,
                "labels": ns.metadata.labels,
                "annotations": ns.metadata.annotations
            })
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return namespace_list
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/namespaces/{namespace}")
async def get_namespace(
    request: Request,
    namespace: str = Path(..., description="The name of the namespace")
):
    """
    Get details of a specific namespace
    """
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Getting details for namespace {namespace}")
        v1 = client.CoreV1Api()
        ns = v1.read_namespace(name=namespace)
        
        namespace_info = {
            "name": ns.metadata.name,
            "status": ns.status.phase,
            "creation_time": ns.metadata.creation_timestamp,
            "labels": ns.metadata.labels,
            "annotations": ns.metadata.annotations,
            "resource_quota": {},
            "limit_range": {}
        }
        
        # Get resource quotas
        try:
            quotas = v1.list_namespaced_resource_quota(namespace=namespace)
            for quota in quotas.items:
                namespace_info["resource_quota"][quota.metadata.name] = {
                    "hard": quota.spec.hard,
                    "used": quota.status.used if quota.status else {}
                }
        except client.rest.ApiException:
            pass
        
        # Get limit ranges
        try:
            limits = v1.list_namespaced_limit_range(namespace=namespace)
            for limit in limits.items:
                namespace_info["limit_range"][limit.metadata.name] = {
                    "limits": [item.to_dict() for item in limit.spec.limits]
                }
        except client.rest.ApiException:
            pass
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return namespace_info
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Namespace {namespace} not found"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.post("/namespaces")
async def create_namespace(
    request: Request,
    namespace_data: NamespaceCreate = Body(...)
):
    """
    Create a new namespace
    """
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Creating namespace {namespace_data.namespace}")
        v1 = client.CoreV1Api()
        
        namespace_manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace_data.namespace,
                "labels": namespace_data.labels or {},
                "annotations": namespace_data.annotations or {}
            }
        }
        
        ns = v1.create_namespace(body=namespace_manifest)
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {
            "message": f"Namespace {ns.metadata.name} created successfully",
            "name": ns.metadata.name,
            "status": ns.status.phase
        }
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 409:
            raise HTTPException(
                status_code=409,
                detail=f"Namespace {namespace_data.namespace} already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.put("/namespaces/{namespace}")
async def update_namespace(
    request: Request,
    namespace: str = Path(..., description="The name of the namespace"),
    namespace_data: NamespaceUpdate = Body(...)
):
    """
    Update a namespace's labels and annotations
    """
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Updating namespace {namespace}")
        v1 = client.CoreV1Api()
        
        # Get current namespace
        current_ns = v1.read_namespace(name=namespace)
        
        # Update labels and annotations
        if namespace_data.labels is not None:
            current_ns.metadata.labels = namespace_data.labels
        if namespace_data.annotations is not None:
            current_ns.metadata.annotations = namespace_data.annotations
        
        # Update the namespace
        ns = v1.patch_namespace(
            name=namespace,
            body=current_ns
        )
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {
            "message": f"Namespace {namespace} updated successfully",
            "name": ns.metadata.name,
            "labels": ns.metadata.labels,
            "annotations": ns.metadata.annotations
        }
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Namespace {namespace} not found"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.delete("/namespaces/{namespace}")
async def delete_namespace(
    request: Request,
    namespace: str = Path(..., description="The name of the namespace")
):
    """
    Delete a namespace and all its resources
    """
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Deleting namespace {namespace}")
        v1 = client.CoreV1Api()
        v1.delete_namespace(name=namespace)
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Namespace {namespace} deleted successfully"}
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Namespace {namespace} not found"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1
