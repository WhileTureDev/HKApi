import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from models.helmRepositoryModel import HelmRepository as HelmRepositoryModel
from schemas.helmRepositorySchema import HelmRepositoryCreate, HelmRepository as HelmRepositorySchema
from utils.database import get_db
from utils.auth import get_current_active_user
from models.userModel import User as UserModel
from utils.helm import add_helm_repo, update_helm_repositories, search_helm_charts, list_helm_charts_in_repo

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/helm/repositories", response_model=HelmRepositorySchema)
def create_helm_repository(
    repository: HelmRepositoryCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.username} is creating a new Helm repository: {repository.name}")
    db_repo = db.query(HelmRepositoryModel).filter_by(name=repository.name).first()
    if db_repo:
        logger.warning(f"Repository {repository.name} already exists")
        raise HTTPException(status_code=400, detail="Repository already exists")

    if not add_helm_repo(repository.name, repository.url):
        logger.error(f"Failed to add Helm repository {repository.name}")
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
    logger.info(f"Helm repository {repository.name} created successfully")
    return new_repository

@router.get("/helm/repositories", response_model=List[HelmRepositorySchema])
def list_helm_repositories(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.username} is listing all Helm repositories")
    repositories = db.query(HelmRepositoryModel).all()
    logger.info(f"Found {len(repositories)} repositories")
    return [HelmRepositorySchema.from_orm(repo) for repo in repositories]

@router.delete("/helm/repositories/{repo_id}", response_model=HelmRepositorySchema)
def delete_helm_repository(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.username} is deleting Helm repository with ID {repo_id}")
    repository = db.query(HelmRepositoryModel).filter_by(id=repo_id).first()
    if not repository:
        logger.warning(f"Repository with ID {repo_id} not found")
        raise HTTPException(status_code=404, detail="Repository not found")

    db.delete(repository)
    db.commit()
    logger.info(f"Helm repository with ID {repo_id} deleted successfully")
    return repository

@router.get("/helm/charts/search", response_model=List[dict])
def search_charts(
    term: str = Query(..., description="The search term for the charts"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.username} is searching for charts with term {term}")
    # Get all repository names from the database
    repositories = db.query(HelmRepositoryModel.name).all()
    repo_names = [repo[0] for repo in repositories]

    # Perform the search
    search_results = search_helm_charts(term, repo_names)
    if not search_results:
        logger.warning(f"No charts found matching the search term {term}")
        raise HTTPException(status_code=404, detail="No charts found matching the search term")
    logger.info(f"Found {len(search_results)} charts matching the search term {term}")
    return search_results

@router.post("/helm/repositories/update", response_model=dict)
def update_repositories(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.username} is updating all Helm repositories")
    success = update_helm_repositories()
    if not success:
        logger.error("Failed to update Helm repositories")
        raise HTTPException(status_code=500, detail="Failed to update Helm repositories")
    logger.info("Helm repositories updated successfully")
    return {"message": "Helm repositories updated successfully"}

@router.get("/helm/repositories/charts", response_model=List[dict])
def list_charts_in_repo(
    repo_name: str = Query(..., description="The name of the repository"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    logger.info(f"User {current_user.username} is listing all charts in repository {repo_name}")
    # Check if the repository exists in the database
    helm_repo = db.query(HelmRepositoryModel).filter_by(name=repo_name).first()
    if not helm_repo:
        logger.warning(f"Repository {repo_name} not found")
        raise HTTPException(status_code=404, detail="Repository not found")

    # List all charts in the specified repository
    charts = list_helm_charts_in_repo(repo_name)
    if not charts:
        logger.warning(f"No charts found in repository {repo_name}")
        raise HTTPException(status_code=404, detail="No charts found in the repository")
    logger.info(f"Found {len(charts)} charts in repository {repo_name}")
    return charts
