from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from models.helmRepositoryModel import HelmRepository as HelmRepositoryModel
from schemas.helmRepositorySchema import HelmRepositoryCreate, HelmRepository as HelmRepositorySchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from utils.helm import add_helm_repo

router = APIRouter()

@router.post("/helm/repositories", response_model=HelmRepositorySchema)
def create_helm_repository(
    repository: HelmRepositoryCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    db_repo = db.query(HelmRepositoryModel).filter_by(name=repository.name).first()
    if db_repo:
        raise HTTPException(status_code=400, detail="Repository already exists")

    if not add_helm_repo(repository.name, repository.url):
        raise HTTPException(status_code=500, detail="Failed to add Helm repository")

    new_repository = HelmRepositoryModel(
        name=repository.name,
        url=repository.url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_repository)
    db.commit()
    db.refresh(new_repository)
    return new_repository

@router.get("/helm/repositories", response_model=List[HelmRepositorySchema])
def list_helm_repositories(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    return db.query(HelmRepositoryModel).all()

@router.delete("/helm/repositories/{repo_id}", response_model=HelmRepositorySchema)
def delete_helm_repository(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    repository = db.query(HelmRepositoryModel).filter_by(id=repo_id).first()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    db.delete(repository)
    db.commit()
    return repository
