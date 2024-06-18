# controllers/changeLogController.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from models.changeLogModel import ChangeLog as ChangeLogModel
from schemas.changeLogSchema import ChangeLog as ChangeLogSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from models.namespaceModel import Namespace as NamespaceModel
from models.projectModel import Project as ProjectModel
from utils.security import get_current_user_roles, is_admin

router = APIRouter()
logger = logging.getLogger(__name__)

def get_resource_details(db: Session, resource: str, resource_id: int) -> (Optional[str], Optional[str]):
    try:
        if resource == 'project':
            project = db.query(ProjectModel).filter(ProjectModel.id == resource_id).first()
            return project.name if project else None, None
        elif resource == 'namespace':
            namespace = db.query(NamespaceModel).filter(NamespaceModel.id == resource_id).first()
            project_name = db.query(ProjectModel).filter(ProjectModel.id == namespace.project_id).first().name if namespace else None
            return namespace.name if namespace else None, project_name
        elif resource == 'user':
            user = db.query(UserModel).filter(UserModel.id == resource_id).first()
            return user.username if user else None, None
        # Add more resources as needed
    except Exception as e:
        logger.error(f"Error getting resource details: {e}")
    return None, None

@router.get("/changelogs", response_model=List[ChangeLogSchema])
async def get_all_change_logs(
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    if not is_admin(current_user_roles):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    change_logs = db.query(ChangeLogModel).all()

    result = []
    for log in change_logs:
        try:
            user = db.query(UserModel).filter(UserModel.id == log.user_id).first()
            resource_name, project_name = get_resource_details(db, log.resource, log.resource_id)
            result.append({
                "id": log.id,
                "user_id": log.user_id,
                "user_name": user.username if user else "Unknown",
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "resource_name": resource_name if resource_name else "Unknown",
                "project_name": project_name if project_name else "Unknown",
                "timestamp": log.timestamp,
                "details": log.details
            })
        except Exception as e:
            logger.error(f"Error processing log entry {log.id}: {e}")
    return result

@router.get("/changelogs/user/{user_id}", response_model=List[ChangeLogSchema])
async def get_change_logs_for_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    if not is_admin(current_user_roles) and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    change_logs = db.query(ChangeLogModel).filter(ChangeLogModel.user_id == user_id).all()

    result = []
    for log in change_logs:
        try:
            user = db.query(UserModel).filter(UserModel.id == log.user_id).first()
            resource_name, project_name = get_resource_details(db, log.resource, log.resource_id)
            result.append({
                "id": log.id,
                "user_id": log.user_id,
                "user_name": user.username if user else "Unknown",
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "resource_name": resource_name if resource_name else "Unknown",
                "project_name": project_name if project_name else "Unknown",
                "timestamp": log.timestamp,
                "details": log.details
            })
        except Exception as e:
            logger.error(f"Error processing log entry {log.id}: {e}")
    return result

@router.get("/changelogs/resource/{resource}/{resource_name}", response_model=List[ChangeLogSchema])
async def get_change_logs_for_resource(
        resource: str,
        resource_name: str,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    if not is_admin(current_user_roles):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Assuming you have a function to get resource ID by name
    resource_id = get_resource_id_by_name(db, resource, resource_name)
    if resource_id is None:
        raise HTTPException(status_code=404, detail=f"{resource} with name {resource_name} not found")

    change_logs = db.query(ChangeLogModel).filter(ChangeLogModel.resource == resource, ChangeLogModel.resource_id == resource_id).all()

    result = []
    for log in change_logs:
        try:
            user = db.query(UserModel).filter(UserModel.id == log.user_id).first()
            resource_name, project_name = get_resource_details(db, log.resource, log.resource_id)
            result.append({
                "id": log.id,
                "user_id": log.user_id,
                "user_name": user.username if user else "Unknown",
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "resource_name": resource_name if resource_name else "Unknown",
                "project_name": project_name if project_name else "Unknown",
                "timestamp": log.timestamp,
                "details": log.details
            })
        except Exception as e:
            logger.error(f"Error processing log entry {log.id}: {e}")
    return result

def get_resource_id_by_name(db: Session, resource: str, resource_name: str) -> Optional[int]:
    try:
        if resource == 'project':
            project = db.query(ProjectModel).filter(ProjectModel.name == resource_name).first()
            return project.id if project else None
        elif resource == 'namespace':
            namespace = db.query(NamespaceModel).filter(NamespaceModel.name == resource_name).first()
            return namespace.id if namespace else None
        elif resource == 'user':
            user = db.query(UserModel).filter(UserModel.username == resource_name).first()
            return user.id if user else None
        # Add more resources as needed
    except Exception as e:
        logger.error(f"Error getting resource ID by name: {e}")
    return None
