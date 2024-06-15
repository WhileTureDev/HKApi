from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from models.projectModel import Project as ProjectModel
from schemas.projectSchema import ProjectCreate, Project as ProjectSchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel

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
def list_projects(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    projects = db.query(ProjectModel).filter(ProjectModel.owner_id == current_user.id).all()
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")
    return projects
