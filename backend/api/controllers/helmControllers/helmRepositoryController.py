# controllers/helmControllers/helmRepositoryController.py

import logging
from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel
from utils.helm import (
    add_helm_repo,
    update_helm_repositories,
    search_helm_charts,
    list_helm_charts_in_repo,
    helm_repositories,
    configure_helm_repositories
)
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS
)
from utils.error_handling import handle_general_exception
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for repositories
helm_repositories = {}

class HelmRepository(BaseModel):
    name: str
    url: str

REQUEST_COUNT = 0
REQUEST_LATENCY = 0
IN_PROGRESS = 0
ERROR_COUNT = 0

@router.post("/helm/repositories", response_model=Dict[str, str])
async def create_helm_repository(
    request: Request,
    repository: HelmRepository,
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Creating a new Helm repository: {repository.name}")
        # Add to Helm
        success = add_helm_repo(repository.name, repository.url)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add Helm repository")
        
        # Store in memory
        helm_repositories[repository.name] = repository.url
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Successfully added repository {repository.name}"}
    except Exception as e:
        ERROR_COUNT += 1
        return handle_general_exception(e, method, endpoint, start_time)
    finally:
        IN_PROGRESS -= 1

@router.get("/helm/repositories", response_model=Dict[str, str])
async def get_helm_repositories(request: Request):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info("Getting all Helm repositories")
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return helm_repositories
    except Exception as e:
        ERROR_COUNT += 1
        return handle_general_exception(e, method, endpoint, start_time)
    finally:
        IN_PROGRESS -= 1

@router.delete("/helm/repositories/{repo_name}")
async def delete_helm_repository(
    request: Request,
    repo_name: str,
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Deleting Helm repository: {repo_name}")
        if repo_name not in helm_repositories:
            raise HTTPException(status_code=404, detail=f"Repository {repo_name} not found")
        
        try:
            # Remove from Helm
            subprocess.run(["helm", "repo", "remove", repo_name], check=True)
            # Remove from memory
            del helm_repositories[repo_name]
            REQUEST_COUNT += 1
            REQUEST_LATENCY += time.time() - start_time
            return {"message": f"Successfully deleted repository {repo_name}"}
        except Exception as e:
            ERROR_COUNT += 1
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        ERROR_COUNT += 1
        return handle_general_exception(e, method, endpoint, start_time)
    finally:
        IN_PROGRESS -= 1

@router.get("/helm/repositories/{repo_name}/charts")
async def list_charts_in_repo(
    request: Request,
    repo_name: str,
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Listing charts in repository: {repo_name}")
        if repo_name not in helm_repositories:
            raise HTTPException(status_code=404, detail=f"Repository {repo_name} not found")
        charts = list_helm_charts_in_repo(repo_name)
        if charts is None:
            raise HTTPException(status_code=500, detail="Failed to list charts")
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return charts
    except Exception as e:
        ERROR_COUNT += 1
        return handle_general_exception(e, method, endpoint, start_time)
    finally:
        IN_PROGRESS -= 1

@router.get("/helm/repositories/search")
async def search_charts(
    request: Request,
    term: str = Query(..., description="The search term for the charts"),
):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info(f"Searching for Helm charts with term: {term}")
        search_results = search_helm_charts(term, list(helm_repositories.keys()))
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return search_results
    except Exception as e:
        ERROR_COUNT += 1
        return handle_general_exception(e, method, endpoint, start_time)
    finally:
        IN_PROGRESS -= 1

@router.post("/helm/repositories/update")
async def update_repositories(request: Request):
    global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    IN_PROGRESS += 1

    try:
        logger.info("Updating all Helm repositories")
        if not update_helm_repositories():
            raise HTTPException(status_code=500, detail="Failed to update repositories")
        
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": "Repositories updated successfully"}
    except Exception as e:
        ERROR_COUNT += 1
        return handle_general_exception(e, method, endpoint, start_time)
    finally:
        IN_PROGRESS -= 1
