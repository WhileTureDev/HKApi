# controllers/userControllers/namespaceController.py

import logging
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List

from models.namespaceModel import Namespace as NamespaceModel
from models.projectModel import Project as ProjectModel
from models.deploymentModel import Deployment as DeploymentModel
from schemas.namespaceSchema import NamespaceCreate, Namespace as NamespaceSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from utils.circuit_breaker import call_database_operation
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)
from kubernetes import client, config

router = APIRouter()
logger = logging.getLogger(__name__)

def generate_unique_namespace_name(project_name: str, db: Session) -> str:
    """
    Generate a unique namespace name based on the project name.
    Ensures no duplicate namespace names exist.
    """
    # Sanitize project name to be k8s namespace compliant
    base_name = project_name.lower().replace(' ', '-')[:30]
    
    # Add a unique identifier to ensure uniqueness
    unique_suffix = str(uuid.uuid4())[:8]
    namespace_name = f"{base_name}-{unique_suffix}"
    
    # Check if namespace already exists
    existing_namespace = db.query(NamespaceModel).filter_by(name=namespace_name).first()
    while existing_namespace:
        unique_suffix = str(uuid.uuid4())[:8]
        namespace_name = f"{base_name}-{unique_suffix}"
        existing_namespace = db.query(NamespaceModel).filter_by(name=namespace_name).first()
    
    return namespace_name

def create_kubernetes_namespace(namespace_name: str):
    """
    Create a namespace in Kubernetes cluster
    """
    try:
        # Load Kubernetes configuration
        config.load_kube_config()
        
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

@router.post("/", response_model=NamespaceSchema)
def create_namespace(
    request: Request,
    namespace_data: NamespaceCreate,  
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a new namespace for a project
    """
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        # Check if project exists and belongs to the user
        project = db.query(ProjectModel).filter(
            ProjectModel.id == namespace_data.project_id,
            ProjectModel.owner_id == current_user.id
        ).first()

        if not project:
            logger.warning(f"Project {namespace_data.project_id} not found or not owned by user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or not owned by you"
            )

        # Check if namespace already exists
        existing_namespace = db.query(NamespaceModel).filter(
            NamespaceModel.name == namespace_data.name,
            NamespaceModel.project_id == project.id
        ).first()

        if existing_namespace:
            logger.warning(f"Namespace {namespace_data.name} already exists for project {project.name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Namespace with this name already exists for the project"
            )

        # Create namespace in Kubernetes
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_data.name))
            v1.create_namespace(namespace)
        except Exception as k8s_error:
            logger.error(f"Failed to create Kubernetes namespace {namespace_data.name}: {str(k8s_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Kubernetes namespace: {str(k8s_error)}"
            )

        # Create namespace in database
        new_namespace = NamespaceModel(
            name=namespace_data.name,
            project_id=project.id,
            owner_id=current_user.id
        )

        call_database_operation(lambda: db.add(new_namespace))
        call_database_operation(lambda: db.commit())
        call_database_operation(lambda: db.refresh(new_namespace))

        logger.info(f"Namespace {namespace_data.name} created for project {project.name} by user {current_user.username}")

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return new_namespace

    except HTTPException as e:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise

    except Exception as e:
        logger.error(f"Unexpected error while creating namespace: {str(e)}")
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the namespace"
        )
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/", response_model=List[NamespaceSchema])
def list_namespaces(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    List namespaces owned by the current user
    """
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        namespaces = db.query(NamespaceModel).filter(
            NamespaceModel.owner_id == current_user.id
        ).all()

        logger.info(f"Found {len(namespaces)} namespaces for user {current_user.username}")

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return namespaces

    except Exception as e:
        logger.error(f"Error listing namespaces: {str(e)}")
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing namespaces"
        )
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.delete("/{namespace_id}", response_model=NamespaceSchema)
def delete_namespace(
    request: Request,
    namespace_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Delete a namespace
    """
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        # Find the namespace and verify ownership
        namespace = db.query(NamespaceModel).filter(
            NamespaceModel.id == namespace_id,
            NamespaceModel.owner_id == current_user.id
        ).first()

        if not namespace:
            logger.warning(f"Namespace {namespace_id} not found or not owned by user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Namespace not found or not owned by you"
            )

        # Check if the namespace has any active deployments
        active_deployments = db.query(DeploymentModel).filter(
            DeploymentModel.namespace_id == namespace.id,
            DeploymentModel.status.in_(['running', 'pending', 'creating'])
        ).count()

        if active_deployments > 0:
            logger.warning(f"Cannot delete namespace {namespace.name} with active deployments")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete namespace with active deployments"
            )

        # Delete namespace from Kubernetes
        try:
            config.load_kube_config()
            v1 = client.CoreV1Api()
            v1.delete_namespace(namespace.name)
        except client.exceptions.ApiException as k8s_error:
            # If namespace doesn't exist in Kubernetes, log and continue
            if k8s_error.status == 404:
                logger.info(f"Namespace {namespace.name} not found in Kubernetes, proceeding with database deletion")
            else:
                logger.error(f"Failed to delete Kubernetes namespace {namespace.name}: {str(k8s_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete Kubernetes namespace: {str(k8s_error)}"
                )

        # Delete namespace from database
        call_database_operation(lambda: db.delete(namespace))
        call_database_operation(lambda: db.commit())

        logger.info(f"Namespace {namespace.name} deleted by user {current_user.username}")

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        
        return namespace

    except HTTPException as http_exc:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise

    except Exception as e:
        logger.error(f"Unexpected error while deleting namespace: {str(e)}")
        db.rollback()
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the namespace"
        )
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()
