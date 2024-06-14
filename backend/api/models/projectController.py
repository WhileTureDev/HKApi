from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models import Project
from ..utils.database import get_db

router = APIRouter()

@router.post("/projects/")
def create_project(project: Project, db: Session = Depends(get_db)):
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
