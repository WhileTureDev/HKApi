# controllers/helmController.py

import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Request
import json
import yaml
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import datetime
import tempfile
import os
from models.deploymentModel import Deployment as DeploymentModel
from models.helmRepositoryModel import HelmRepository as HelmRepositoryModel
from models.projectModel import Project as ProjectModel
from models.namespaceModel import Namespace as NamespaceModel
from schemas.deploymentSchema import Deployment as DeploymentSchema, RollbackOptions
from utils.change_logger import log_change
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from utils.security import check_project_and_namespace_ownership, get_current_user_roles, is_admin
from utils.circuit_breaker import call_database_operation
from utils.helm import (
    deploy_helm_chart_combined,
    delete_helm_release,
    list_helm_releases,
    get_helm_values,
    rollback_helm_release,
    get_helm_status,
    add_helm_repo,
    extract_repo_name_from_url,
    get_helm_release_history,
    list_all_helm_releases,
    get_helm_release_notes,
    export_helm_release_values_to_file
)
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)
from utils.error_handling import handle_general_exception

router = APIRouter()
logger = logging.getLogger(__name__)

def deployment_to_dict(deployment: DeploymentModel) -> dict:
    return {
        "id": deployment.id,
        "project": deployment.project,
        "install_type": deployment.install_type,
        "release_name": deployment.release_name,
        "chart_name": deployment.chart_name,
        "chart_repo_url": deployment.chart_repo_url,
        "namespace_id": deployment.namespace_id,
        "namespace_name": deployment.namespace_name,
        "values": deployment.values,
        "revision": deployment.revision,
        "active": deployment.active,
        "status": deployment.status,
        "created_at": deployment.created_at,
        "updated_at": deployment.updated_at,
        "owner_id": deployment.owner_id
    }

@router.post("/helm/releases", response_model=DeploymentSchema)
async def create_release(
        request: Request,
        release_name: str = Query(..., description="The name of the release"),
        chart_name: str = Query(..., description="The name of the chart"),
        chart_repo_url: str = Query(..., description="The URL of the chart repository"),
        namespace: str = Query(..., description="The namespace of the release"),
        project: Optional[str] = Query(None, description="The project name"),
        values: Optional[str] = Query(None, description="The values for the chart in JSON format"),
        version: Optional[str] = Query(None, description="The version of the chart"),
        debug: Optional[bool] = Query(False, description="Enable debug mode"),
        values_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Starting release creation process for {release_name} in project {project if project else 'N/A'}")

        # Admins can access any project and namespace
        if not is_admin(current_user_roles):
            project_obj, namespace_obj = check_project_and_namespace_ownership(db, project, namespace, current_user)
        else:
            project_obj = call_database_operation(lambda: db.query(ProjectModel).filter_by(name=project).first())
            namespace_obj = call_database_operation(lambda: db.query(NamespaceModel).filter_by(name=namespace).first())

        # Parse the values JSON if provided
        values_dict = json.loads(values) if values else {}
        logger.debug(f"Parsed values: {values_dict}")

        # Save the uploaded values file to a temporary location if provided
        values_file_path = None
        if values_file:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(values_file.file.read())
                values_file_path = tmp.name
            logger.debug(f"Saved values file to {values_file_path}")

            # Load values from the file if no values JSON was provided
            if not values:
                with open(values_file_path, 'r') as f:
                    values_dict = yaml.safe_load(f)
                logger.debug(f"Loaded values from file: {values_dict}")

        # If the namespace does not exist, create it
        if not namespace_obj:
            namespace_obj = NamespaceModel(
                name=namespace,
                project_id=project_obj.id if project_obj else None,
                owner_id=current_user.id,  # Set the owner_id
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            call_database_operation(lambda: db.add(namespace_obj))
            call_database_operation(lambda: db.commit())
            call_database_operation(lambda: db.refresh(namespace_obj))
            logger.info(f"Created new namespace: {namespace}")

        # Extract the repository name from the URL
        repo_name = extract_repo_name_from_url(chart_repo_url)
        logger.debug(f"Extracted repo name: {repo_name}")

        # Check if the Helm repository exists in the database
        helm_repo = call_database_operation(lambda: db.query(HelmRepositoryModel).filter_by(name=repo_name).first())
        if not helm_repo:
            # Add the repository to the database
            new_repo = HelmRepositoryModel(
                name=repo_name,
                url=chart_repo_url,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            call_database_operation(lambda: db.add(new_repo))
            call_database_operation(lambda: db.commit())
            call_database_operation(lambda: db.refresh(new_repo))
            logger.info(f"Added new Helm repository: {repo_name}")

            # Add the repository to Helm
            if not add_helm_repo(repo_name, chart_repo_url):
                logger.error("Failed to add Helm repository")
                raise HTTPException(status_code=500, detail="Failed to add Helm repository")

        # Deploy Helm chart using the combined function
        revision = deploy_helm_chart_combined(
            release_name=release_name,
            chart_name=chart_name,
            chart_repo_url=chart_repo_url,
            namespace=namespace,
            values=values_dict,
            values_file_path=values_file_path,
            version=version,
            debug=debug
        )

        if revision == -1:
            logger.error(f"Helm chart deployment failed for release {release_name}")
            raise HTTPException(status_code=500, detail="Helm chart deployment failed")

        # Clean up the temporary file
        if values_file_path:
            os.remove(values_file_path)
            logger.debug(f"Deleted temporary values file: {values_file_path}")

        # Create a new deployment record for each revision
        new_deployment = DeploymentModel(
            project=project,
            release_name=release_name,
            chart_name=chart_name,
            chart_repo_url=chart_repo_url,
            namespace_id=namespace_obj.id,
            namespace_name=namespace,
            values=values_dict if values_dict is not None else {},  # Store the values if provided
            revision=revision,
            install_type="helm",
            active=True,
            status="deployed",
            owner_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        call_database_operation(lambda: db.add(new_deployment))
        call_database_operation(lambda: db.commit())
        call_database_operation(lambda: db.refresh(new_deployment))

        # Log the change with resource_name and project_name, including additional details
        details = (f"Created release '{release_name}' using chart '{chart_name}' from repo '{chart_repo_url}' in "
                   f"namespace '{namespace}' with revision {revision}.")
        log_change(db, current_user.id, action="create", resource="release", resource_id=str(new_deployment.id),
                   resource_name=release_name, project_name=project, details=details)

        logger.info(f"Successfully created release: {release_name}")
        return new_deployment
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error deploying Helm chart: {e}")
        handle_general_exception(e)
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.delete("/helm/releases", response_model=DeploymentSchema)
def delete_release(
        request: Request,
        release_name: str = Query(..., description="The name of the release to delete"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "DELETE"
    endpoint = "/helm/releases"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Attempting to delete release {release_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace,
                owner_id=current_user.id,
                active=True
            ).first())
            if not deployment:
                logger.error(
                    f"Deployment {release_name} not found for user {current_user.username} in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")
        else:
            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace,
                active=True
            ).first())
            if not deployment:
                logger.error(f"Deployment {release_name} not found in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")

        success = delete_helm_release(release_name, namespace)
        if not success:
            logger.error(f"Helm release {release_name} not found in namespace {namespace}")
            raise HTTPException(status_code=404, detail="Helm release not found")

        deployment.active = False
        deployment.status = "deleted"
        deployment.updated_at = datetime.utcnow()
        call_database_operation(lambda: db.commit())
        call_database_operation(lambda: db.refresh(deployment))
        logger.info(f"Marked deployment {release_name} as deleted in database")

        log_change(db, current_user.id, "delete", "release", deployment.id, release_name, deployment.project)

        return deployment
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"Error deleting Helm chart: {e}")
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/helm/releases", response_model=List[dict])
async def list_releases(
        request: Request,
        namespace: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "GET"
    endpoint = "/helm/releases"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Listing releases in namespace {namespace if namespace else 'all namespaces'}")

        releases = []
        if namespace:
            if not is_admin(current_user_roles):
                _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)
                releases = list_helm_releases(namespace)
            else:
                releases = list_helm_releases(namespace)
        else:
            if not is_admin(current_user_roles):
                namespaces = call_database_operation(lambda: db.query(NamespaceModel).filter_by(owner_id=current_user.id).all())
                for ns in namespaces:
                    releases.extend(list_helm_releases(ns.name))
            else:
                releases = list_all_helm_releases()

        if not releases:
            logger.warning(f"No releases found in namespace {namespace if namespace else 'all namespaces'}")
            raise HTTPException(status_code=404, detail="No releases found")
        return releases
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"Error listing Helm releases: {e}")
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/helm/releases/values", response_model=dict)
async def get_release_values(
        request: Request,
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "GET"
    endpoint = "/helm/releases/values"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Getting values for release {release_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)

            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace,
                owner_id=current_user.id
            ).first())
            if not deployment:
                logger.error(
                    f"Deployment {release_name} not found for user {current_user.username} in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")
        else:
            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace
            ).first())
            if not deployment:
                logger.error(f"Deployment {release_name} not found in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")

        values = get_helm_values(release_name, namespace)
        if not values:
            logger.warning(f"Values not found for release {release_name} in namespace {namespace}")
            raise HTTPException(status_code=404, detail="Release values not found")
        return values
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"Error getting Helm release values: {e}")
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.post("/helm/releases/rollback")
async def rollback_release(
        request: Request,
        release_name: str = Query(..., description="The name of the release"),
        revision: int = Query(..., description="The revision number to rollback to"),
        namespace: str = Query(..., description="The namespace of the release"),
        options: RollbackOptions = Depends(),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "POST"
    endpoint = "/helm/releases/rollback"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Rolling back release {release_name} in namespace {namespace} to revision {revision}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)

            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace,
                owner_id=current_user.id
            ).first())
            if not deployment:
                logger.error(
                    f"Deployment {release_name} not found for user {current_user.username} in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")
        else:
            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace
            ).first())
            if not deployment:
                logger.error(f"Deployment {release_name} not found in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")

        success = rollback_helm_release(
            release_name, revision, namespace, force=options.force, recreate_pods=options.recreate_pods
        )
        if not success:
            logger.error(f"Rollback failed for release {release_name} to revision {revision} in namespace {namespace}")
            raise HTTPException(status_code=500, detail="Rollback failed")

        deployment.updated_at = datetime.utcnow()
        call_database_operation(lambda: db.commit())
        call_database_operation(lambda: db.refresh(deployment))
        logger.info(f"Updated deployment {release_name} to reflect rollback to revision {revision}")

        return {"message": "Rollback successful"}
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"Error rolling back Helm release: {e}")
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/helm/releases/status", response_model=dict)
async def get_release_status(
        request: Request,
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "GET"
    endpoint = "/helm/releases/status"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Getting status for release {release_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)

            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace,
                owner_id=current_user.id
            ).first())
            if not deployment:
                logger.error(
                    f"Deployment {release_name} not found for user {current_user.username} in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")
        else:
            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace
            ).first())
            if not deployment:
                logger.error(f"Deployment {release_name} not found in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")

        status = get_helm_status(release_name, namespace)
        if not status:
            logger.warning(f"Status not found for release {release_name} in namespace {namespace}")
            raise HTTPException(status_code=404, detail="Release status not found")
        return status
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"Error getting Helm release status: {e}")
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/helm/releases/history", response_model=List[dict])
async def get_release_history(
        request: Request,
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "GET"
    endpoint = "/helm/releases/history"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Getting history for release {release_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)

            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace,
                owner_id=current_user.id
            ).first())
            if not deployment:
                logger.error(
                    f"Deployment {release_name} not found for user {current_user.username} in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")
        else:
            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace
            ).first())
            if not deployment:
                logger.error(f"Deployment {release_name} not found in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")

        history = get_helm_release_history(release_name, namespace)
        if not history:
            logger.warning(f"History not found for release {release_name} in namespace {namespace}")
            raise HTTPException(status_code=404, detail="Release history not found")
        return history
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"Error getting Helm release history: {e}")
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/helm/releases/notes", response_model=dict)
async def get_release_notes(
        request: Request,
        release_name: str = Query(..., description="The name of the release"),
        revision: int = Query(..., description="The revision number"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "GET"
    endpoint = "/helm/releases/notes"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Getting notes for release {release_name}, revision {revision} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)

            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace,
                owner_id=current_user.id
            ).first())
            if not deployment:
                logger.error(
                    f"Deployment {release_name} not found for user {current_user.username} in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")
        else:
            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace
            ).first())
            if not deployment:
                logger.error(f"Deployment {release_name} not found in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")

        notes = get_helm_release_notes(release_name, revision, namespace)
        if not notes:
            logger.warning(f"Notes not found for release {release_name}, revision {revision} in namespace {namespace}")
            raise HTTPException(status_code=404, detail="Release notes not found")
        return {"notes": notes}
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"Error getting Helm release notes: {e}")
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/helm/releases/export")
async def export_release_values(
        request: Request,
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "GET"
    endpoint = "/helm/releases/export"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Exporting values for release {release_name} in namespace {namespace}")

        if not is_admin(current_user_roles):
            _, namespace_obj = check_project_and_namespace_ownership(db, None, namespace, current_user)

            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace,
                owner_id=current_user.id
            ).first())
            if not deployment:
                logger.error(
                    f"Deployment {release_name} not found for user {current_user.username} in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")
        else:
            deployment = call_database_operation(lambda: db.query(DeploymentModel).filter_by(
                release_name=release_name,
                namespace_name=namespace
            ).first())
            if not deployment:
                logger.error(f"Deployment {release_name} not found in namespace {namespace}")
                raise HTTPException(status_code=404, detail="Helm release not found")

        file_path = export_helm_release_values_to_file(release_name, namespace)
        if not file_path:
            logger.error(f"Error exporting values for release {release_name} in namespace {namespace}")
            raise HTTPException(status_code=500, detail="Error exporting release values")
        logger.info(f"Successfully exported values for release {release_name} to file {file_path}")
        return FileResponse(
            path=file_path,
            filename=f"{release_name}-values.yaml",
            media_type='application/octet-stream'
        )
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"Error exporting Helm release values: {e}")
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/helm/releases/all", response_model=List[dict])
async def list_all_releases(
        request: Request,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    method = "GET"
    endpoint = "/helm/releases/all"
    start_time = time.time()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"Listing all releases for user {current_user.username}")

        if not is_admin(current_user_roles):
            deployments = call_database_operation(lambda: db.query(DeploymentModel).filter_by(owner_id=current_user.id).all())
        else:
            deployments = call_database_operation(lambda: db.query(DeploymentModel).all())

        if not deployments:
            logger.warning(f"No releases found for user {current_user.username}")
            raise HTTPException(status_code=404, detail="No releases found")

        releases = [deployment_to_dict(deployment) for deployment in deployments]

        return releases
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"Error listing all Helm releases: {e}")
        handle_general_exception(e)
    finally:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
