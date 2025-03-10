# controllers/k8sControllers/deploymentController.py

import logging
import time
import yaml
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File
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
from utils.error_handling import handle_general_exception

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
            raise HTTPException(status_code=e.status, detail=e.body)

    except Exception as e:
        logger.error(f"An error occurred while listing deployments: {str(e)}")
        handle_general_exception(e)
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
            raise HTTPException(status_code=e.status, detail=e.body)

    except Exception as e:
        logger.error(f"An error occurred while fetching deployment details: {str(e)}")
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()


@router.post("/deployment")
async def create_deployment(
        namespace: str = Form(..., description="The namespace to create the deployment in"),
        deployment_name: Optional[str] = Form(None, description="The name of the deployment"),
        image: Optional[str] = Form(None, description="The image for the deployment"),
        replicas: int = Form(1, description="The number of replicas"),
        yaml_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "POST"
    endpoint = "/deployment"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is creating a deployment in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        apps_v1 = client.AppsV1Api()

        if yaml_file:
            try:
                deployment_yaml = yaml.safe_load(yaml_file.file.read())
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML file: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid YAML file")
        else:
            if not deployment_name or not image:
                raise HTTPException(status_code=400,
                                    detail="Deployment name and image are required if no YAML file is provided")

            deployment_yaml = {
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
                                    "image": image,
                                    "ports": [{"containerPort": 80}]
                                }
                            ]
                        }
                    }
                }
            }

        try:
            deployment = apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment_yaml)
            logger.info(
                f"User {current_user.username} successfully created deployment {deployment.metadata.name} in namespace"
                f" {namespace}")

            # Log the change with resource_name and project_name, including additional details
            namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
            project_obj = db.query(ProjectModel).filter_by(id=namespace_obj.project_id).first()
            log_change(
                db,
                current_user.id,
                action="create",
                resource="deployment",
                resource_id=deployment.metadata.uid,  # Use deployment.metadata.uid as resource_id
                resource_name=deployment.metadata.name,
                project_name=project_obj.name if project_obj else "N/A",
                details=f"Deployment {deployment.metadata.name} created in namespace {namespace}"
            )

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

            return deployment_details
        except client.exceptions.ApiException as e:
            if e.status == 409:
                logger.error(f"Deployment {deployment_name} already exists in namespace {namespace}")
                raise HTTPException(status_code=409,
                                    detail=f"Deployment {deployment_name} already exists in namespace {namespace}")
            else:
                logger.error(f"Error creating deployment {deployment_name} in namespace {namespace}: {str(e)}")
                raise HTTPException(status_code=e.status, detail=e.body)
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while creating the deployment: {str(e)}")
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()


@router.put("/deployment")
async def update_deployment(
        namespace: str = Form(..., description="The namespace to update the deployment in"),
        deployment_name: Optional[str] = Form(None, description="The name of the deployment"),
        image: Optional[str] = Form(None, description="The image for the deployment"),
        replicas: Optional[int] = Form(None, description="The number of replicas"),
        yaml_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "PUT"
    endpoint = "/deployment"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is updating a deployment in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        apps_v1 = client.AppsV1Api()

        if yaml_file:
            try:
                deployment_yaml = yaml.safe_load(yaml_file.file.read())
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML file: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid YAML file")
        else:
            if not deployment_name or not image or replicas is None:
                raise HTTPException(status_code=400,
                                    detail="Deployment name, image, and replicas are required if no YAML file is "
                                           "provided")

            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            deployment.spec.replicas = replicas
            for container in deployment.spec.template.spec.containers:
                if container.name == deployment_name:
                    container.image = image

            deployment_yaml = deployment

        try:
            updated_deployment = apps_v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace,
                                                                     body=deployment_yaml)
            logger.info(
                f"User {current_user.username} successfully updated deployment {updated_deployment.metadata.name} in "
                f"namespace {namespace}")

            # Log the change with resource_name and project_name, including additional details
            namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
            project_obj = db.query(ProjectModel).filter_by(id=namespace_obj.project_id).first()
            log_change(
                db,
                current_user.id,
                action="update",
                resource="deployment",
                resource_id=updated_deployment.metadata.uid,  # Use updated_deployment.metadata.uid as resource_id
                resource_name=updated_deployment.metadata.name,
                project_name=project_obj.name if project_obj else "N/A",
                details=f"Deployment {updated_deployment.metadata.name} updated in namespace {namespace}"
            )

            deployment_details = {
                "name": updated_deployment.metadata.name,
                "namespace": updated_deployment.metadata.namespace,
                "replicas": updated_deployment.spec.replicas,
                "available_replicas": updated_deployment.status.available_replicas,
                "unavailable_replicas": updated_deployment.status.unavailable_replicas,
                "updated_replicas": updated_deployment.status.updated_replicas,
                "strategy": updated_deployment.spec.strategy.type,
                "conditions": [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "last_update_time": condition.last_update_time,
                        "last_transition_time": condition.last_transition_time,
                        "reason": condition.reason,
                        "message": condition.message
                    } for condition in updated_deployment.status.conditions or []
                ]
            }

            return deployment_details
        except client.exceptions.ApiException as e:
            if e.status == 404:
                logger.error(f"Deployment {deployment_name} not found in namespace {namespace}")
                raise HTTPException(status_code=404,
                                    detail=f"Deployment {deployment_name} not found in namespace {namespace}")
            else:
                logger.error(f"Error updating deployment {deployment_name} in namespace {namespace}: {str(e)}")
                raise HTTPException(status_code=e.status, detail=e.body)
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while updating the deployment: {str(e)}")
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.delete("/deployment")
async def delete_deployment(
    namespace: str = Query(..., description="The namespace of the deployment"),
    deployment_name: str = Query(..., description="The name of the deployment"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "DELETE"
    endpoint = "/deployment"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is deleting deployment {deployment_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        apps_v1 = client.AppsV1Api()

        try:
            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            apps_v1.delete_namespaced_deployment(name=deployment_name, namespace=namespace)
            logger.info(f"User {current_user.username} successfully deleted deployment {deployment_name} in namespace"
                        f" {namespace}")

            # Log the change with resource_name and project_name, including additional details
            namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
            project_obj = db.query(ProjectModel).filter_by(id=namespace_obj.project_id).first()
            log_change(
                db,
                current_user.id,
                action="delete",
                resource="deployment",
                resource_id=deployment.metadata.uid,  # Use deployment.metadata.uid as resource_id
                resource_name=deployment.metadata.name,
                project_name=project_obj.name if project_obj else "N/A",
                details=f"Deployment {deployment.metadata.name} deleted in namespace {namespace}"
            )

            return {"message": f"Deployment {deployment_name} deleted successfully"}
        except client.exceptions.ApiException as e:
            if e.status == 404:
                logger.error(f"Deployment {deployment_name} not found in namespace {namespace}")
                raise HTTPException(status_code=404, detail=f"Deployment {deployment_name} not found in namespace "
                                                            f"{namespace}")
            else:
                logger.error(f"Error deleting deployment {deployment_name} in namespace {namespace}: {str(e)}")
                raise HTTPException(status_code=e.status, detail=e.body)
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while deleting the deployment: {str(e)}")
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()


@router.get("/deployment/revisions")
async def get_deployment_revisions(
    namespace: str = Query(..., description="The namespace of the deployment"),
    deployment_name: str = Query(..., description="The name of the deployment"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "GET"
    endpoint = "/deployment/revisions"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is fetching revision history for deployment {deployment_name} "
                    f"in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        apps_v1 = client.AppsV1Api()
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        if not deployment.metadata.annotations:
            raise HTTPException(status_code=404, detail="No revision history found for this deployment")

        revisions = deployment.metadata.annotations.get("deployment.kubernetes.io/revision", None)
        if revisions is None:
            raise HTTPException(status_code=404, detail="No revision history found for this deployment")

        # Get revision details from the ReplicaSets
        replica_sets = apps_v1.list_namespaced_replica_set(namespace=namespace)
        revision_history = []
        for rs in replica_sets.items:
            if rs.metadata.owner_references and rs.metadata.owner_references[0].name == deployment_name:
                revision_history.append({
                    "revision": rs.metadata.annotations.get("deployment.kubernetes.io/revision"),
                    "name": rs.metadata.name,
                    "created_at": rs.metadata.creation_timestamp
                })

        revision_history.sort(key=lambda x: int(x["revision"]), reverse=True)

        logger.info(f"User {current_user.username} successfully fetched revision history for deployment "
                    f"{deployment_name} in namespace {namespace}")
        return {"revisions": revision_history}
    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"Deployment {deployment_name} not found in namespace {namespace}")
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_name} "
                                                        f"not found in namespace {namespace}")
        else:
            logger.error(f"Error fetching revision history for deployment {deployment_name} "
                         f"in namespace {namespace}: {str(e)}")
            raise HTTPException(status_code=e.status, detail=e.body)
    except Exception as e:
        logger.error(f"An error occurred while fetching revision history: {str(e)}")
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.post("/deployment/rollout")
async def deployment_rollout(
    namespace: str = Form(..., description="The namespace of the deployment"),
    deployment_name: str = Form(..., description="The name of the deployment"),
    action: str = Form(..., description="The rollout action to perform", regex="^(restart|rollback)$"),
    revision: Optional[int] = Form(None, description="The revision to rollback to (required for rollback action)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = "POST"
    endpoint = "/deployment/rollout"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    namespace_obj = None  # Initialize namespace_obj here
    deployment = None  # Initialize deployment here

    try:
        logger.info(f"User {current_user.username} is performing rollout action {action} on deployment "
                    f"{deployment_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            if not namespace_obj:
                raise HTTPException(status_code=403, detail="Not enough permissions to access this namespace")

        apps_v1 = client.AppsV1Api()

        if action == "restart":
            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            deployment.spec.template.metadata.annotations = {"kubectl.kubernetes.io/restartedAt": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
            apps_v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=deployment)
        elif action == "rollback":
            if revision is None:
                raise HTTPException(status_code=400, detail="Revision number is required for rollback action")

            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)

            # Scale the deployment to zero replicas
            scale = client.V1Scale(
                spec=client.V1ScaleSpec(replicas=0)
            )
            apps_v1.patch_namespaced_deployment_scale(name=deployment_name, namespace=namespace, body=scale)

            # Patch the deployment with the specified revision
            patch_body = {
                "spec": {
                    "revisionHistoryLimit": revision
                }
            }
            apps_v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=patch_body)

            # Scale the deployment back up to the original replicas count
            original_replicas = deployment.spec.replicas
            scale.spec.replicas = original_replicas
            apps_v1.patch_namespaced_deployment_scale(name=deployment_name, namespace=namespace, body=scale)

        logger.info(f"User {current_user.username} successfully performed rollout action {action} on deployment "
                    f"{deployment_name} in namespace {namespace}")

        # Log the change
        log_change(
            db,
            current_user.id,
            action=action,
            resource="deployment",
            resource_id=deployment.metadata.uid if deployment else "N/A",  # Ensure deployment.metadata.uid is accessed safely
            resource_name=deployment_name,
            project_name=namespace_obj.name if namespace_obj else "N/A",
            details=f"Rollout action {action} performed on deployment {deployment_name} in namespace {namespace}"
        )

        return {"message": f"Rollout action {action} successfully performed on deployment {deployment_name}"}

    except client.exceptions.ApiException as e:
        logger.error(f"Error performing rollout action {action} on deployment {deployment_name} in namespace {namespace}: {str(e)}")
        if e.status == 404:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_name} not found in namespace {namespace}")
        elif e.status == 409:
            raise HTTPException(status_code=409, detail=f"Conflict occurred: {e.body}")
        elif e.status == 422:
            raise HTTPException(status_code=422, detail=f"Unprocessable entity: {e.body}")
        else:
            raise HTTPException(status_code=e.status, detail=e.body)
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while performing rollout action: {str(e)}")
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
