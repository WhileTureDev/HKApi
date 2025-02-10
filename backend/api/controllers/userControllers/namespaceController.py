import logging
import os
import time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List

from models.namespaceModel import Namespace as NamespaceModel
from models.projectModel import Project as ProjectModel
from schemas.namespaceSchema import NamespaceCreate, Namespace as NamespaceSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel

# Optional Kubernetes imports
try:
    from kubernetes import client, config
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)

# Check if Kubernetes namespace creation is enabled via environment variable
ENABLE_KUBERNETES_NAMESPACE = os.getenv('ENABLE_KUBERNETES_NAMESPACE', 'true').lower() == 'true'

def create_kubernetes_namespace(namespace_name: str):
    """
    Create a namespace in Kubernetes cluster
    """
    # Skip if Kubernetes is not available or not enabled
    if not KUBERNETES_AVAILABLE or not ENABLE_KUBERNETES_NAMESPACE:
        logger.info(f"Skipping Kubernetes namespace creation. Kubernetes available: {KUBERNETES_AVAILABLE}, Enabled: {ENABLE_KUBERNETES_NAMESPACE}")
        return

    try:
        # Try in-cluster configuration first
        try:
            config.load_incluster_config()
        except config.ConfigException:
            # If not in a cluster, try loading from default location
            try:
                config.load_kube_config()
            except Exception as e:
                logger.error(f"Failed to load Kubernetes configuration: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load Kubernetes configuration: {str(e)}"
                )
        
        # Create Kubernetes API client
        v1 = client.CoreV1Api()
        
        # Create namespace object
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_name))
        
        # Create the namespace
        v1.create_namespace(namespace)
        
        logger.info(f"Kubernetes namespace {namespace_name} created successfully")
    except Exception as e:
        logger.error(f"Failed to create Kubernetes namespace {namespace_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Kubernetes namespace: {str(e)}"
        )

@router.get("/list", response_model=List[NamespaceSchema])
def list_namespaces(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    List namespaces owned by the current user
    """
    namespaces = db.query(NamespaceModel).filter(
        NamespaceModel.owner_id == current_user.id
    ).all()
    return namespaces

@router.post("/create", response_model=NamespaceSchema)
def create_namespace(
    namespace_data: NamespaceCreate,  
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a new namespace
    """
    # Attempt to create Kubernetes namespace if enabled
    try:
        create_kubernetes_namespace(namespace_data.name)
    except HTTPException as k8s_error:
        # Log the Kubernetes namespace creation error but continue
        logger.warning(f"Kubernetes namespace creation failed: {k8s_error.detail}")

    # Create namespace in database
    new_namespace = NamespaceModel(
        name=namespace_data.name,
        project_id=namespace_data.project_id,
        owner_id=current_user.id
    )

    db.add(new_namespace)
    db.commit()
    db.refresh(new_namespace)
    return new_namespace

@router.delete("/delete/{namespace_id}", response_model=NamespaceSchema)
def delete_namespace(
    namespace_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Delete a namespace
    """
    namespace = db.query(NamespaceModel).filter(
        NamespaceModel.id == namespace_id,
        NamespaceModel.owner_id == current_user.id
    ).first()

    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Namespace not found or not owned by you"
        )

    # Attempt to delete Kubernetes namespace if enabled
    if KUBERNETES_AVAILABLE and ENABLE_KUBERNETES_NAMESPACE:
        try:
            config.load_incluster_config()
        except config.ConfigException:
            # If not in a cluster, try loading from default location
            try:
                config.load_kube_config()
            except Exception as e:
                logger.error(f"Failed to load Kubernetes configuration: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load Kubernetes configuration: {str(e)}"
                )

        v1 = client.CoreV1Api()
        try:
            v1.delete_namespace(namespace.name)
        except client.exceptions.ApiException as k8s_error:
            # If namespace doesn't exist in Kubernetes, log and continue
            if k8s_error.status != 404:
                logger.error(f"Failed to delete Kubernetes namespace {namespace.name}: {str(k8s_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete Kubernetes namespace: {str(k8s_error)}"
                )

    # Delete namespace from database
    db.delete(namespace)
    db.commit()
    return namespace
