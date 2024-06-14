from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..models.projectModel import Project as ProjectModel
from ..models.userModel import User as UserModel  # Correct import
from ..schemas.projectSchema import ProjectCreate, Project as ProjectSchema
from ..utils.database import get_db
from ..utils.auth import get_current_active_user
from datetime import datetime

router = APIRouter()


@router.post("/projects/", response_model=ProjectSchema)
def create_project(
        project: ProjectCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    new_project = ProjectModel(
        name=project.name,
        description=project.description,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


@router.get("/projects/", response_model=List[ProjectSchema])
def read_projects(
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
    return db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id).all()
