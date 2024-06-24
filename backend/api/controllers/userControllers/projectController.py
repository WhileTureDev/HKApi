# controllers/projectControllers/projectController.py

import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Request
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
            raise HTTPException(status_code=400, detail="Project with this name already exists")

        new_project = ProjectModel(
            name=project.name,
            description=project.description,
            owner_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        call_database_operation(lambda: db.add(new_project))
        call_database_operation(lambda: db.commit())
        call_database_operation(lambda: db.refresh(new_project))
        logger.info(f"Project {project.name} created successfully")
        return new_project
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while creating the project: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

@router.get("/projects/", response_model=List[ProjectSchema])
def list_projects(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        logger.info(f"User {current_user.username} is listing all their projects")
        projects = call_database_operation(lambda: db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id).all())
        if not projects:
            logger.warning(f"No projects found for user {current_user.username}")
            raise HTTPException(status_code=404, detail="No projects found")
        logger.info(f"Found {len(projects)} projects for user {current_user.username}")
        return projects
    except HTTPException as http_exc:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while listing projects: {str(e)}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="An internal error occurred")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
