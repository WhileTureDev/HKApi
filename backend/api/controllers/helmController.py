from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from models.deploymentModel import Deployment as DeploymentModel
from models.helmRepositoryModel import HelmRepository as HelmRepositoryModel
from models.projectModel import Project as ProjectModel
from models.namespaceModel import Namespace as NamespaceModel
from schemas.deploymentSchema import DeploymentCreate, Deployment as DeploymentSchema
from schemas.helmRepositorySchema import HelmRepositoryCreate
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
    get_helm_release_history  # Add this import
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
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    success = rollback_helm_release(release_name, revision, namespace)
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
