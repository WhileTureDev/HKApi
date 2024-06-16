import logging
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
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
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
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

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/helm/releases", response_model=DeploymentSchema)
async def create_release(
        release_name: str = Query(..., description="The name of the release"),
        chart_name: str = Query(..., description="The name of the chart"),
        chart_repo_url: str = Query(..., description="The URL of the chart repository"),
        namespace: str = Query(..., description="The namespace of the release"),
        project: str = Query(..., description="The project name"),
        values: Optional[str] = Query(None, description="The values for the chart in JSON format"),
        version: Optional[str] = Query(None, description="The version of the chart"),
        debug: Optional[bool] = Query(False, description="Enable debug mode"),
        values_file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    try:
        logger.info(f"Starting release creation process for {release_name} in project {project}")

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

        # Check if the project exists
        project_obj = db.query(ProjectModel).filter_by(name=project, owner_id=current_user.id).first()
        if not project_obj:
            logger.error(f"Project {project} not found for user {current_user.username}")
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if the namespace exists, if not create it
        namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
        if not namespace_obj:
            namespace_obj = NamespaceModel(
                name=namespace,
                project_id=project_obj.id,  # Use project ID
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(namespace_obj)
            db.commit()
            db.refresh(namespace_obj)
            logger.info(f"Created new namespace: {namespace}")

        # Extract the repository name from the URL
        repo_name = extract_repo_name_from_url(chart_repo_url)
        logger.debug(f"Extracted repo name: {repo_name}")

        # Check if the Helm repository exists in the database
        helm_repo = db.query(HelmRepositoryModel).filter_by(name=repo_name).first()
        if not helm_repo:
            # Add the repository to the database
            new_repo = HelmRepositoryModel(
                name=repo_name,
                url=chart_repo_url,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_repo)
            db.commit()
            db.refresh(new_repo)
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
        db.add(new_deployment)

        db.commit()
        db.refresh(new_deployment)

        logger.info(f"Successfully created release: {release_name}")
        return new_deployment
    except Exception as e:
        logger.error(f"Error deploying Helm chart: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deploying Helm chart: {str(e)}")


@router.delete("/helm/releases", response_model=DeploymentSchema)
def delete_release(
        release_name: str = Query(..., description="The name of the release to delete"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"Attempting to delete release {release_name} in namespace {namespace}")
    # Delete Helm release using utility function
    success = delete_helm_release(release_name, namespace)
    if not success:
        logger.error(f"Helm release {release_name} not found in namespace {namespace}")
        raise HTTPException(status_code=404, detail="Helm release not found")

    # Mark the deployment as inactive
    deployment = db.query(DeploymentModel).filter_by(
        release_name=release_name,
        namespace_name=namespace,
        owner_id=current_user.id,
        active=True
    ).first()

    if deployment:
        deployment.active = False
        deployment.status = "deleted"
        deployment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(deployment)
        logger.info(f"Marked deployment {release_name} as deleted in database")

    return deployment


@router.get("/helm/releases", response_model=List[dict])
async def list_releases(
        namespace: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"Listing releases in namespace {namespace if namespace else 'all namespaces'}")
    releases = list_helm_releases(namespace)
    if not releases:
        logger.warning(f"No releases found in namespace {namespace if namespace else 'all namespaces'}")
        raise HTTPException(status_code=404, detail="No releases found")
    return releases


@router.get("/helm/releases/values", response_model=dict)
async def get_release_values(
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"Getting values for release {release_name} in namespace {namespace}")
    values = get_helm_values(release_name, namespace)
    if not values:
        logger.warning(f"Values not found for release {release_name} in namespace {namespace}")
        raise HTTPException(status_code=404, detail="Release values not found")
    return values


@router.post("/helm/releases/rollback")
async def rollback_release(
        release_name: str = Query(..., description="The name of the release"),
        revision: int = Query(..., description="The revision number to rollback to"),
        namespace: str = Query(..., description="The namespace of the release"),
        options: RollbackOptions = Depends(),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"Rolling back release {release_name} in namespace {namespace} to revision {revision}")
    success = rollback_helm_release(
        release_name, revision, namespace, force=options.force, recreate_pods=options.recreate_pods
    )
    if not success:
        logger.error(f"Rollback failed for release {release_name} to revision {revision} in namespace {namespace}")
        raise HTTPException(status_code=500, detail="Rollback failed")

    # Update the deployment record to reflect the rollback
    deployment = db.query(DeploymentModel).filter_by(
        release_name=release_name,
        namespace_name=namespace,
        revision=revision,
        owner_id=current_user.id
    ).first()

    if deployment:
        deployment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(deployment)
        logger.info(f"Updated deployment {release_name} to reflect rollback to revision {revision}")

    return {"message": "Rollback successful"}


@router.get("/helm/releases/status", response_model=dict)
async def get_release_status(
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"Getting status for release {release_name} in namespace {namespace}")
    status = get_helm_status(release_name, namespace)
    if not status:
        logger.warning(f"Status not found for release {release_name} in namespace {namespace}")
        raise HTTPException(status_code=404, detail="Release status not found")
    return status


@router.get("/helm/releases/history", response_model=List[dict])
async def get_release_history(
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"Getting history for release {release_name} in namespace {namespace}")
    history = get_helm_release_history(release_name, namespace)
    if not history:
        logger.warning(f"History not found for release {release_name} in namespace {namespace}")
        raise HTTPException(status_code=404, detail="Release history not found")
    return history


@router.get("/helm/releases/all", response_model=List[dict])
async def list_all_releases(
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    logger.info("Listing all releases across all namespaces")
    releases = list_all_helm_releases()
    if not releases:
        logger.warning("No releases found across all namespaces")
        raise HTTPException(status_code=404, detail="No releases found")
    return releases


@router.get("/helm/releases/notes", response_model=dict)
async def get_release_notes(
        release_name: str = Query(..., description="The name of the release"),
        revision: int = Query(..., description="The revision number"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"Getting notes for release {release_name}, revision {revision} in namespace {namespace}")
    notes = get_helm_release_notes(release_name, revision, namespace)
    if not notes:
        logger.warning(f"Notes not found for release {release_name}, revision {revision} in namespace {namespace}")
        raise HTTPException(status_code=404, detail="Release notes not found")
    return {"notes": notes}


@router.get("/helm/releases/export")
async def export_release_values(
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"Exporting values for release {release_name} in namespace {namespace}")
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
