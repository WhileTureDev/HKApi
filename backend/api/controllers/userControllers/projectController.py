# controllers/projectControllers/projectController.py

import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from models.projectModel import Project as ProjectModel
from schemas.projectSchema import ProjectCreate, Project as ProjectSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from utils.circuit_breaker import call_database_operation
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/projects/", response_model=ProjectSchema)
def create_project(
    request: Request,
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is creating a new project: {project.name}")

        # Check if project with the same name already exists
        existing_project = call_database_operation(lambda: db.query(ProjectModel).filter(ProjectModel.name == project.name).first())
        if existing_project:
            logger.warning(f"Project with name {project.name} already exists")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project with this name already exists")

        # Create project without relationships first
        new_project = ProjectModel(
            name=project.name,
            description=project.description,
            owner_id=current_user.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add and commit project first
        call_database_operation(lambda: db.add(new_project))
        call_database_operation(lambda: db.commit())
        call_database_operation(lambda: db.refresh(new_project))
        
        logger.info(f"Project {new_project.name} created by user {current_user.username}")

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return new_project

    except HTTPException as http_exc:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise

    except Exception as e:
        logger.error(f"An error occurred while creating the project: {str(e)}")
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/projects/", response_model=List[ProjectSchema])
def list_projects(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    try:
        logger.info(f"User {current_user.username} is listing all their projects")
        # Only select the fields we need, avoiding relationship loading
        projects = (
            db.query(
                ProjectModel.id,
                ProjectModel.name,
                ProjectModel.description,
                ProjectModel.created_at,
                ProjectModel.updated_at,
                ProjectModel.owner_id,
            )
            .filter(ProjectModel.owner_id == current_user.id)
            .all()
        )
        
        # Convert to list of Project objects
        project_list = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "owner_id": p.owner_id,
            }
            for p in projects
        ]
        
        logger.info(f"Found {len(project_list)} projects for user {current_user.username}")
        return project_list
    except Exception as e:
        logger.error(f"An error occurred while listing projects: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is attempting to delete project {project_id}")

        # Get the project
        project = call_database_operation(
            lambda: db.query(ProjectModel)
            .filter(ProjectModel.id == project_id)
            .first()
        )

        # Check if project exists
        if not project:
            logger.warning(f"Project {project_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check if user is the owner
        if project.owner_id != current_user.id:
            logger.warning(f"User {current_user.username} attempted to delete project {project_id} but is not the owner")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the project owner can delete this project"
            )

        # Delete the project
        call_database_operation(lambda: db.delete(project))
        call_database_operation(lambda: db.commit())

        logger.info(f"Project {project_id} successfully deleted by user {current_user.username}")

        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        return None

    except HTTPException as e:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise

    except Exception as e:
        logger.error(f"Unexpected error while deleting project: {str(e)}")
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the project"
        )
    finally:
        IN_PROGRESS.labels(endpoint=endpoint).dec()
