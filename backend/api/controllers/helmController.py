import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
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
from schemas.deploymentSchema import DeploymentCreate, Deployment as DeploymentSchema, RollbackOptions
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from utils.helm import (
    deploy_helm_chart,
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
    export_helm_release_values_to_file,
    deploy_helm_chart_with_file  # Add this import
)

router = APIRouter()

@router.post("/helm/releases", response_model=DeploymentSchema)
def create_release(
        deployment: DeploymentCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # Check if the project exists
    project = db.query(ProjectModel).filter_by(name=deployment.project, owner_id=current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if the namespace exists, if not create it
    namespace = db.query(NamespaceModel).filter_by(name=deployment.namespace_name).first()
    if not namespace:
        namespace = NamespaceModel(
            name=deployment.namespace_name,
            project_id=project.id,  # Use project ID
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(namespace)
        db.commit()
        db.refresh(namespace)

    # Extract the repository name from the URL
    repo_name = extract_repo_name_from_url(deployment.chart_repo_url)

    # Check if the Helm repository exists in the database
    helm_repo = db.query(HelmRepositoryModel).filter_by(name=repo_name).first()
    if not helm_repo:
        # Add the repository to the database
        new_repo = HelmRepositoryModel(
            name=repo_name,
            url=deployment.chart_repo_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_repo)
        db.commit()
        db.refresh(new_repo)
        # Add the repository to Helm
        if not add_helm_repo(repo_name, deployment.chart_repo_url):
            raise HTTPException(status_code=500, detail="Failed to add Helm repository")

    # Deploy Helm chart using utility function
    revision = deploy_helm_chart(
        release_name=deployment.release_name,
        chart_name=deployment.chart_name,
        chart_repo_url=deployment.chart_repo_url,
        namespace=deployment.namespace_name,
        values=deployment.values,  # Pass the custom values
        version=deployment.version  # Pass the version if provided
    )
    if revision == -1:
        raise HTTPException(status_code=500, detail="Helm chart deployment failed")

    # Create a new deployment record for each revision
    new_deployment = DeploymentModel(
        project=deployment.project,
        release_name=deployment.release_name,  # Use release_name instead of chart_name
        chart_name=deployment.chart_name,  # Ensure chart_name is set
        chart_repo_url=deployment.chart_repo_url,
        namespace_id=namespace.id,
        namespace_name=deployment.namespace_name,
        values=deployment.values,
        revision=revision,
        install_type="helm",
        active=True,
        status="deployed",  # Set status to deployed
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_deployment)

    db.commit()
    db.refresh(new_deployment)
    return new_deployment


@router.delete("/helm/releases", response_model=DeploymentSchema)
def delete_release(
        release_name: str = Query(..., description="The name of the release to delete"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    # Delete Helm release using utility function
    success = delete_helm_release(release_name, namespace)
    if not success:
        raise HTTPException(status_code=404, detail="Helm release not found")

    # Mark the deployment as inactive
    deployment = db.query(DeploymentModel).filter_by(
        release_name=release_name,  # Use release_name instead of chart_name
        namespace_name=namespace,
        owner_id=current_user.id,
        active=True
    ).first()

    if deployment:
        deployment.active = False
        deployment.status = "deleted"  # Set status to deleted
        deployment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(deployment)

    return deployment


@router.get("/helm/releases", response_model=List[dict])
async def list_releases(
        namespace: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    releases = list_helm_releases(namespace)
    if not releases:
        raise HTTPException(status_code=404, detail="No releases found")
    return releases


@router.get("/helm/releases/values", response_model=dict)
async def get_release_values(
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    values = get_helm_values(release_name, namespace)
    if not values:
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
    success = rollback_helm_release(
        release_name, revision, namespace, force=options.force, recreate_pods=options.recreate_pods
    )
    if not success:
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

    return {"message": "Rollback successful"}


@router.get("/helm/releases/status", response_model=dict)
async def get_release_status(
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    status = get_helm_status(release_name, namespace)
    if not status:
        raise HTTPException(status_code=404, detail="Release status not found")
    return status


@router.get("/helm/releases/history", response_model=List[dict])
async def get_release_history(
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    history = get_helm_release_history(release_name, namespace)
    if not history:
        raise HTTPException(status_code=404, detail="Release history not found")
    return history


@router.get("/helm/releases/all", response_model=List[dict])
async def list_all_releases(
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    releases = list_all_helm_releases()
    if not releases:
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
    notes = get_helm_release_notes(release_name, revision, namespace)
    if not notes:
        raise HTTPException(status_code=404, detail="Release notes not found")
    return {"notes": notes}


@router.get("/helm/releases/export")
async def export_release_values(
        release_name: str = Query(..., description="The name of the release"),
        namespace: str = Query(..., description="The namespace of the release"),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    file_path = export_helm_release_values_to_file(release_name, namespace)
    if not file_path:
        raise HTTPException(status_code=500, detail="Error exporting release values")
    return FileResponse(
        path=file_path,
        filename=f"{release_name}-values.yaml",
        media_type='application/octet-stream'
    )


@router.post("/helm/releases/import")
async def import_release_values(
        release_name: str = Query(..., description="The name of the release"),
        chart_name: str = Query(..., description="The name of the chart"),
        chart_repo_url: str = Query(..., description="The URL of the chart repository"),
        namespace: str = Query(..., description="The namespace of the release"),
        project: str = Query(..., description="The name of the project"),
        version: Optional[str] = Query(None, description="The version of the chart"),
        values_file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    try:
        # Check if the project exists
        project_obj = db.query(ProjectModel).filter_by(name=project, owner_id=current_user.id).first()
        if not project_obj:
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

        # Extract the repository name from the URL
        repo_name = extract_repo_name_from_url(chart_repo_url)

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
            # Add the repository to Helm
            if not add_helm_repo(repo_name, chart_repo_url):
                raise HTTPException(status_code=500, detail="Failed to add Helm repository")

        # Save the uploaded file to a temporary location and read the values
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(values_file.file.read())
            tmp_path = tmp.name

        with open(tmp_path, 'r') as file:
            values = yaml.safe_load(file)

        # Deploy Helm chart using the uploaded values file
        revision = deploy_helm_chart_with_file(
            release_name=release_name,
            chart_name=chart_name,
            chart_repo_url=chart_repo_url,
            namespace=namespace,
            values_file_path=tmp_path,
            version=version
        )

        if revision == -1:
            raise HTTPException(status_code=500, detail="Helm chart deployment failed")

        # Clean up the temporary file
        os.remove(tmp_path)

        # Create a new deployment record for each revision
        new_deployment = DeploymentModel(
            project=project,
            release_name=release_name,
            chart_name=chart_name,
            chart_repo_url=chart_repo_url,
            namespace_id=namespace_obj.id,
            namespace_name=namespace,
            values=values,  # Store the values in the database
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

        # Return a success message
        return {"message": "Helm chart deployed successfully", "revision": revision}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error importing release values: {str(e)}")
