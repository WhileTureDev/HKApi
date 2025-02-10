# controllers/projectControllers/projectController.py

import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List
from models.projectModel import Project as ProjectModel
from models.userModel import User as UserModel
from models.userProjectModel import UserProject
from models.namespaceModel import Namespace
from schemas.projectSchema import (
    ProjectCreate, Project, ProjectResponse,
    ProjectDeleteResponse, UserBase
)
from utils.database import get_db
from utils.auth import get_current_active_user
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/projects/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: Request,
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> ProjectResponse:
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is creating a new project: {project.name}")

        # Check if project with the same name already exists
        existing_project = db.query(ProjectModel).filter(ProjectModel.name == project.name).first()
        if existing_project:
            logger.warning(f"Project with name {project.name} already exists")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project with this name already exists")

        try:
            # Create new project
            new_project = ProjectModel(
                name=project.name,
                description=project.description,
                owner_id=current_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add and commit project first
            db.add(new_project)
            db.commit()
            db.refresh(new_project)
            
            logger.info(f"Project {new_project.name} created by user {current_user.username}")

            REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
            IN_PROGRESS.labels(endpoint=endpoint).dec()

            # Create response using Pydantic model
            response = ProjectResponse(
                id=new_project.id,
                name=new_project.name,
                description=new_project.description,
                owner_id=new_project.owner_id,
                created_at=new_project.created_at,
                updated_at=new_project.updated_at,
                owner=UserBase(
                    id=current_user.id,
                    username=current_user.username,
                    email=current_user.email,
                    full_name=current_user.full_name
                ),
                message="Project created successfully"
            )
            return response

        except Exception as e:
            db.rollback()
            raise e

    except HTTPException as http_exc:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        IN_PROGRESS.labels(endpoint=endpoint).dec()
        raise

    except Exception as e:
        logger.error(f"An error occurred while creating the project: {str(e)}")
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        IN_PROGRESS.labels(endpoint=endpoint).dec()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")

@router.get("/projects/", response_model=List[Project])
async def list_projects(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> List[Project]:
    try:
        logger.info(f"User {current_user.username} is listing all their projects")
        
        # Get all projects with owner information eagerly loaded
        projects = db.query(ProjectModel)\
            .filter(ProjectModel.owner_id == current_user.id)\
            .join(UserModel)\
            .options(joinedload(ProjectModel.owner))\
            .all()
        
        logger.info(f"Successfully fetched {len(projects)} projects for user {current_user.username}")

        # Convert to list of Project models
        result = []
        for project in projects:
            result.append(Project(
                id=project.id,
                name=project.name,
                description=project.description,
                owner_id=project.owner_id,
                created_at=project.created_at,
                updated_at=project.updated_at,
                owner=UserBase(
                    id=project.owner.id,
                    username=project.owner.username,
                    email=project.owner.email,
                    full_name=project.owner.full_name
                ) if project.owner else None
            ))
        return result

    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching projects"
        )

@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
) -> None:
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is attempting to delete project {project_id}")

        # Get the project
        project = db.query(ProjectModel)\
            .filter(ProjectModel.id == project_id)\
            .first()

        # Check if project exists
        if not project:
            logger.warning(f"Project {project_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
            
        # Check if user has permission to delete the project
        if project.owner_id != current_user.id:
            logger.warning(f"User {current_user.username} does not have permission to delete project {project_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this project"
            )

        project_name = project.name  # Store name before deletion

        try:
            # Delete associated user_projects first
            db.query(UserProject)\
                .filter(UserProject.project_id == project_id)\
                .delete()

            # Delete associated namespaces
            db.query(Namespace)\
                .filter(Namespace.project_id == project_id)\
                .delete()

            # Delete the project
            db.delete(project)
            
            # Commit the transaction
            db.commit()
            
            logger.info(f"Successfully deleted project {project_id}")
            REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
            IN_PROGRESS.labels(endpoint=endpoint).dec()
            
            return None

        except Exception as e:
            db.rollback()
            raise e

    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
