# controllers/userControllers/namespaceController.py

import logging
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

router = APIRouter()
logger = logging.getLogger(__name__)

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

    db.delete(namespace)
    db.commit()
    return namespace
