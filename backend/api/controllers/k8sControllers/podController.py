# controllers/k8sControllers/podController.py

import logging
import time
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Path, Request
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

@router.get("/pods")
async def list_pods(
    request: Request,
    namespace: str = Query(..., description="The namespace to list pods from")
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Listing pods in namespace {namespace}")
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(namespace=namespace)
        
        pod_list = []
        for pod in pods.items:
            pod_list.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "ip": pod.status.pod_ip,
                "node": pod.spec.node_name,
                "containers": [
                    {"name": container.name, "image": container.image}
                    for container in pod.spec.containers
                ]
            })
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return pod_list
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Namespace {namespace} not found")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/pods/{pod_name}")
async def get_pod_details(
    request: Request,
    pod_name: str = Path(..., description="The name of the pod"),
    namespace: str = Query(..., description="The namespace of the pod")
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Getting pod {pod_name} details in namespace {namespace}")
        v1 = client.CoreV1Api()
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        
        pod_info = {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ip": pod.status.pod_ip,
            "node": pod.spec.node_name,
            "start_time": pod.status.start_time,
            "containers": [
                {
                    "name": container.name,
                    "image": container.image,
                    "ready": any(
                        status.ready
                        for status in pod.status.container_statuses
                        if status.name == container.name
                    ) if pod.status.container_statuses else False,
                    "state": next(
                        (status.state.to_dict() 
                         for status in pod.status.container_statuses 
                         if status.name == container.name),
                        {}
                    ) if pod.status.container_statuses else {},
                    "resources": container.resources.to_dict() if container.resources else {},
                    "ports": [
                        {"containerPort": port.container_port, "protocol": port.protocol}
                        for port in (container.ports or [])
                    ]
                }
                for container in pod.spec.containers
            ],
            "labels": pod.metadata.labels,
            "annotations": pod.metadata.annotations
        }
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return pod_info
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Pod {pod_name} not found in namespace {namespace}"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.post("/pods")
async def create_pod(
    request: Request,
    namespace: str = Query(..., description="The namespace to create the pod in"),
    pod_name: str = Query(..., description="The name of the pod"),
    image: str = Query(..., description="The container image to use")
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Creating pod {pod_name} in namespace {namespace}")
        v1 = client.CoreV1Api()
        
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name
            },
            "spec": {
                "containers": [{
                    "name": pod_name,
                    "image": image
                }]
            }
        }
        
        pod = v1.create_namespaced_pod(
            namespace=namespace,
            body=pod_manifest
        )
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Pod {pod.metadata.name} created successfully"}
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Namespace {namespace} not found")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.delete("/pods/{pod_name}")
async def delete_pod(
    request: Request,
    pod_name: str = Path(..., description="The name of the pod"),
    namespace: str = Query(..., description="The namespace of the pod")
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Deleting pod {pod_name} in namespace {namespace}")
        v1 = client.CoreV1Api()
        v1.delete_namespaced_pod(
            name=pod_name,
            namespace=namespace
        )
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Pod {pod_name} deleted successfully"}
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Pod {pod_name} not found in namespace {namespace}"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/pods/{pod_name}/logs")
async def get_pod_logs(
    request: Request,
    pod_name: str = Path(..., description="The name of the pod"),
    namespace: str = Query(..., description="The namespace of the pod"),
    container: Optional[str] = Query(None, description="The name of the container (optional)")
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Getting logs for pod {pod_name} in namespace {namespace}")
        v1 = client.CoreV1Api()
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container
        )
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"logs": logs}
    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Pod {pod_name} not found in namespace {namespace}"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1
