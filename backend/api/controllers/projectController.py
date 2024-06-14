from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.projectModel import Project as ProjectModel
from ..schemas.projectSchema import ProjectCreate, Project as ProjectSchema
from ..utils.database import get_db

router = APIRouter()


@router.post("/projects/", response_model=ProjectSchema)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    new_project = ProjectModel(**project.dict())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project
