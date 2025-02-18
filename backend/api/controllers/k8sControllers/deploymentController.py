# controllers/k8sControllers/deploymentController.py

import logging
import time
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Path, Request, Form, UploadFile, File
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

@router.get("/deployments", response_model=dict)
async def list_deployments(
    request: Request,
    namespace: str = Query(..., description="The namespace to list deployments from"),
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Listing deployments in namespace {namespace}")
        apps_v1 = client.AppsV1Api()
        deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
        
        deployment_list = []
        for deployment in deployments.items:
            deployment_list.append({
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.spec.replicas,
                "available_replicas": deployment.status.available_replicas,
                "ready_replicas": deployment.status.ready_replicas,
                "updated_replicas": deployment.status.updated_replicas,
                "strategy": deployment.spec.strategy.type,
                "containers": [
                    {"name": container.name, "image": container.image}
                    for container in deployment.spec.template.spec.containers
                ],
                "created_at": deployment.metadata.creation_timestamp,
            })

        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"deployments": deployment_list}

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

@router.get("/deployments/{deployment_name}", response_model=dict)
async def get_deployment_details(
    request: Request,
    deployment_name: str = Path(..., description="The name of the deployment"),
    namespace: str = Query(..., description="The namespace of the deployment"),
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Getting details for deployment {deployment_name} in namespace {namespace}")
        apps_v1 = client.AppsV1Api()
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        deployment_details = {
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "replicas": deployment.spec.replicas,
            "available_replicas": deployment.status.available_replicas,
            "ready_replicas": deployment.status.ready_replicas,
            "updated_replicas": deployment.status.updated_replicas,
            "strategy": deployment.spec.strategy.type,
            "containers": [
                {
                    "name": container.name,
                    "image": container.image,
                    "ports": [{"containerPort": port.container_port} for port in container.ports] if container.ports else []
                }
                for container in deployment.spec.template.spec.containers
            ],
            "created_at": deployment.metadata.creation_timestamp,
            "labels": deployment.metadata.labels,
            "annotations": deployment.metadata.annotations
        }

        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return deployment_details

    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_name} not found in namespace {namespace}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.post("/deployments", response_model=dict)
async def create_deployment(
    request: Request,
    namespace: str = Form(..., description="The namespace to create the deployment in"),
    deployment_name: Optional[str] = Form(None, description="The name of the deployment"),
    image: Optional[str] = Form(None, description="The image for the deployment"),
    replicas: int = Form(1, description="The number of replicas"),
    yaml_file: Optional[UploadFile] = File(None),
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Creating deployment in namespace {namespace}")
        apps_v1 = client.AppsV1Api()

        if yaml_file:
            # Parse YAML file content
            yaml_content = await yaml_file.read()
            deployment_dict = yaml.safe_load(yaml_content)
            
            # Ensure it's a Deployment
            if deployment_dict.get("kind") != "Deployment":
                raise HTTPException(status_code=400, detail="YAML file must contain a Deployment resource")
            
            # Create deployment from YAML
            deployment = apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deployment_dict
            )
            created_name = deployment.metadata.name
        else:
            if not deployment_name or not image:
                raise HTTPException(status_code=400, detail="deployment_name and image are required when not using YAML")

            # Create deployment from parameters
            deployment_manifest = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": deployment_name
                },
                "spec": {
                    "replicas": replicas,
                    "selector": {
                        "matchLabels": {
                            "app": deployment_name
                        }
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "app": deployment_name
                            }
                        },
                        "spec": {
                            "containers": [
                                {
                                    "name": deployment_name,
                                    "image": image
                                }
                            ]
                        }
                    }
                }
            }

            deployment = apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deployment_manifest
            )
            created_name = deployment_name

        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Deployment {created_name} created successfully"}

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

@router.put("/deployments/{deployment_name}", response_model=dict)
async def update_deployment(
    request: Request,
    deployment_name: str = Path(..., description="The name of the deployment"),
    namespace: str = Form(..., description="The namespace to update the deployment in"),
    image: Optional[str] = Form(None, description="The image for the deployment"),
    replicas: Optional[int] = Form(None, description="The number of replicas"),
    yaml_file: Optional[UploadFile] = File(None),
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Updating deployment {deployment_name} in namespace {namespace}")
        apps_v1 = client.AppsV1Api()

        if yaml_file:
            # Parse YAML file content
            yaml_content = await yaml_file.read()
            deployment_dict = yaml.safe_load(yaml_content)
            
            # Ensure it's a Deployment
            if deployment_dict.get("kind") != "Deployment":
                raise HTTPException(status_code=400, detail="YAML file must contain a Deployment resource")
            
            # Update deployment from YAML
            deployment = apps_v1.replace_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment_dict
            )
        else:
            # Get existing deployment
            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)

            # Update image if provided
            if image:
                deployment.spec.template.spec.containers[0].image = image

            # Update replicas if provided
            if replicas is not None:
                deployment.spec.replicas = replicas

            # Apply updates
            deployment = apps_v1.replace_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )

        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Deployment {deployment_name} updated successfully"}

    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_name} not found in namespace {namespace}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.delete("/deployments/{deployment_name}", response_model=dict)
async def delete_deployment(
    request: Request,
    deployment_name: str = Path(..., description="The name of the deployment"),
    namespace: str = Query(..., description="The namespace of the deployment"),
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Deleting deployment {deployment_name} in namespace {namespace}")
        apps_v1 = client.AppsV1Api()
        apps_v1.delete_namespaced_deployment(
            name=deployment_name,
            namespace=namespace
        )

        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Deployment {deployment_name} deleted successfully"}

    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_name} not found in namespace {namespace}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/deployments/{deployment_name}/revisions", response_model=dict)
async def get_deployment_revisions(
    request: Request,
    deployment_name: str = Path(..., description="The name of the deployment"),
    namespace: str = Query(..., description="The namespace of the deployment"),
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Getting revision history for deployment {deployment_name} in namespace {namespace}")
        apps_v1 = client.AppsV1Api()
        
        # Get the deployment's replica sets
        rs_list = apps_v1.list_namespaced_replica_set(
            namespace=namespace,
            label_selector=f"app={deployment_name}"
        )
        
        revisions = []
        for rs in rs_list.items:
            if rs.metadata.annotations and "deployment.kubernetes.io/revision" in rs.metadata.annotations:
                revision = {
                    "revision": rs.metadata.annotations["deployment.kubernetes.io/revision"],
                    "replica_set": rs.metadata.name,
                    "created_at": rs.metadata.creation_timestamp,
                    "replicas": rs.spec.replicas,
                    "image": rs.spec.template.spec.containers[0].image
                }
                revisions.append(revision)

        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"revisions": revisions}

    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_name} not found in namespace {namespace}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.post("/deployments/{deployment_name}/rollout", response_model=dict)
async def deployment_rollout(
    request: Request,
    deployment_name: str = Path(..., description="The name of the deployment"),
    namespace: str = Form(..., description="The namespace of the deployment"),
    action: str = Form(..., description="The rollout action to perform", regex="^(restart|rollback)$"),
    revision: Optional[int] = Form(None, description="The revision to rollback to (required for rollback action)"),
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Performing {action} on deployment {deployment_name} in namespace {namespace}")
        apps_v1 = client.AppsV1Api()

        if action == "restart":
            # Patch deployment with a restart annotation
            patch = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": time.strftime('%Y-%m-%d-%H-%M-%S')
                            }
                        }
                    }
                }
            }
            apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=patch
            )
            message = f"Deployment {deployment_name} restart initiated"
        
        elif action == "rollback":
            if revision is None:
                raise HTTPException(status_code=400, detail="Revision is required for rollback action")

            # Rollback to specific revision
            body = {
                "name": deployment_name,
                "rollbackTo": {
                    "revision": revision
                }
            }
            apps_v1.create_namespaced_deployment_rollback(
                name=deployment_name,
                namespace=namespace,
                body=body
            )
            message = f"Deployment {deployment_name} rollback to revision {revision} initiated"

        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": message}

    except client.rest.ApiException as e:
        ERROR_COUNT += 1
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_name} not found in namespace {namespace}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1
