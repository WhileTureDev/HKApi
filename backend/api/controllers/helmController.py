from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from models.deploymentModel import Deployment as DeploymentModel
from schemas.deploymentSchema import DeploymentCreate, Deployment as DeploymentSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from utils.k8s import deploy_helm_chart, delete_helm_release
from models.namespaceModel import Namespace as NamespaceModel
from models.projectModel import Project as ProjectModel

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

    # Deploy Helm chart using utility function
    revision = deploy_helm_chart(
        release_name=deployment.chart_name,
        chart_name=deployment.chart_name,
        chart_repo_url=deployment.chart_repo_url,
        namespace=deployment.namespace_name,
        values=deployment.values  # Pass the custom values
    )
    if revision == -1:
        raise HTTPException(status_code=500, detail="Helm chart deployment failed")

    # Update or create deployment record
    existing_deployment = db.query(DeploymentModel).filter_by(
        project=deployment.project,
        chart_name=deployment.chart_name,
        namespace_name=deployment.namespace_name,
        owner_id=current_user.id
    ).first()

    if existing_deployment:
        existing_deployment.values = deployment.values
        existing_deployment.revision = revision
        existing_deployment.active = True
        existing_deployment.status = "deployed"  # Set status to deployed
        existing_deployment.updated_at = datetime.utcnow()
    else:
        existing_deployment = DeploymentModel(
            project=deployment.project,
            chart_name=deployment.chart_name,
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
        db.add(existing_deployment)

    db.commit()
    db.refresh(existing_deployment)
    return existing_deployment


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
        raise HTTPException(status_code=500, detail="Helm chart deletion failed")

    # Mark the deployment as inactive
    deployment = db.query(DeploymentModel).filter_by(
        chart_name=release_name,
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
