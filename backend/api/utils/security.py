from typing import List, Optional
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from models.namespaceModel import Namespace as NamespaceModel
from models.projectModel import Project as ProjectModel
from models.roleModel import Role
from models.userModel import User as UserModel
from models.userRoleModel import UserRole
from utils.auth import get_current_active_user
from utils.database import get_db
from models.changeLogModel import ChangeLog


def check_project_and_namespace_ownership(db: Session, project: Optional[str], namespace: str, current_user: UserModel):
    project_obj = None

    # Check if the project exists and belongs to the current user if project is provided
    if project:
        project_obj = db.query(ProjectModel).filter_by(name=project, owner_id=current_user.id).first()
        if not project_obj:
            raise HTTPException(status_code=404, detail="Project not found")

    # Check if the namespace exists under any user
    namespace_obj = db.query(NamespaceModel).filter_by(name=namespace).first()
    if namespace_obj and namespace_obj.owner_id != current_user.id:
        # If the namespace exists and does not belong to the current user, raise an exception
        raise HTTPException(status_code=400,
                            detail=f'User {current_user.username} does not own the namespace {namespace}')

    return project_obj, namespace_obj


def get_current_user_roles(current_user: UserModel = Depends(get_current_active_user), db: Session = Depends(get_db)) -> \
List[str]:
    roles = db.query(Role.name).join(UserRole).filter(UserRole.user_id == current_user.id).all()
    return [role.name for role in roles]


def has_role(required_role: str):
    def role_checker(current_user_roles: List[str] = Depends(get_current_user_roles)):
        if required_role not in current_user_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return role_checker


def is_admin(current_user_roles: List[str] = Depends(get_current_user_roles)):
    return "admin" in current_user_roles


def log_change(db: Session, user_id: int, action: str, resource: str, resource_id: int, resource_name: str,
               project_name: str = None, details: str = None):
    change_log = ChangeLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        resource_name=resource_name,
        project_name=project_name,
        details=details
    )
    db.add(change_log)
    db.commit()
