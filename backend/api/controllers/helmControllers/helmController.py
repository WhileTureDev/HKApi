# controllers/helmController.py

import logging
import time
from fastapi import APIRouter, HTTPException, Query, File, UploadFile, Request
import json
import yaml
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
import tempfile
import os
from pydantic import BaseModel
from utils.helm import (
    deploy_helm_chart_combined,
    delete_helm_release,
    list_helm_releases,
    get_helm_values,
    rollback_helm_release,
    get_helm_status,
    add_helm_repo,
    extract_repo_name_from_url,
    get_helm_release_history,
    list_all_helm_releases,
    get_helm_release_notes,
    export_helm_release_values_to_file
)
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS
)

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for deployments
deployments = {}

class RollbackOptions(BaseModel):
    force: bool = False
    recreate_pods: bool = False

class DeploymentCreate(BaseModel):
    release_name: str
    chart_name: str
    chart_repo_url: str
    namespace: str
    values: Optional[Dict] = None
    version: Optional[str] = None
    debug: bool = False

global REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
REQUEST_COUNT = 0
REQUEST_LATENCY = 0
IN_PROGRESS = 0
ERROR_COUNT = 0

@router.post("/releases")
async def create_release(
    request: Request,
    deployment: DeploymentCreate,
    values_file: Optional[UploadFile] = File(None)
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        logger.info(f"Creating new release: {deployment.release_name}")
        
        values_data = None
        if values_file:
            content = await values_file.read()
            values_data = yaml.safe_load(content)
        elif deployment.values:
            values_data = deployment.values

        # Deploy the Helm chart
        success = deploy_helm_chart_combined(
            release_name=deployment.release_name,
            chart_name=deployment.chart_name,
            chart_repo_url=deployment.chart_repo_url,
            namespace=deployment.namespace,
            values=values_data,
            version=deployment.version,
            debug=deployment.debug
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to deploy Helm chart")

        # Store deployment info in memory
        deployments[f"{deployment.namespace}/{deployment.release_name}"] = {
            "release_name": deployment.release_name,
            "chart_name": deployment.chart_name,
            "namespace": deployment.namespace,
            "chart_repo_url": deployment.chart_repo_url
        }

        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Successfully deployed release {deployment.release_name}"}

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error creating release: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.delete("/releases/{release_name}")
async def delete_release(
    request: Request,
    release_name: str,
    namespace: str = Query(..., description="The namespace of the release")
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        logger.info(f"Deleting release: {release_name} from namespace: {namespace}")
        
        # Delete the Helm release
        success = delete_helm_release(release_name, namespace)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete Helm release")

        # Remove from in-memory storage
        deployment_key = f"{namespace}/{release_name}"
        if deployment_key in deployments:
            del deployments[deployment_key]

        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Successfully deleted release {release_name}"}

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error deleting release: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/releases")
async def list_releases(
    request: Request,
    namespace: Optional[str] = None
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        releases = list_helm_releases(namespace)
        
        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return releases

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error listing releases: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/releases/{release_name}/values")
async def get_release_values(
    request: Request,
    release_name: str,
    namespace: str = Query(..., description="The namespace of the release")
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        values = get_helm_values(release_name, namespace)
        if not values:
            raise HTTPException(status_code=404, detail="Release values not found")

        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return values

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error getting release values: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.post("/releases/{release_name}/rollback")
async def rollback_release(
    request: Request,
    release_name: str,
    revision: int = Query(..., description="The revision number to rollback to"),
    namespace: str = Query(..., description="The namespace of the release"),
    options: RollbackOptions = RollbackOptions()
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        success = rollback_helm_release(
            release_name=release_name,
            revision=revision,
            namespace=namespace,
            force=options.force,
            recreate_pods=options.recreate_pods
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to rollback release")

        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"message": f"Successfully rolled back release {release_name} to revision {revision}"}

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error rolling back release: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/releases/{release_name}/status")
async def get_release_status(
    request: Request,
    release_name: str,
    namespace: str = Query(..., description="The namespace of the release")
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        status = get_helm_status(release_name, namespace)
        if not status:
            raise HTTPException(status_code=404, detail="Release status not found")

        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return status

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error getting release status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/releases/{release_name}/history")
async def get_release_history(
    request: Request,
    release_name: str,
    namespace: str = Query(..., description="The namespace of the release")
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        history = get_helm_release_history(release_name, namespace)
        if not history:
            raise HTTPException(status_code=404, detail="Release history not found")

        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return history

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error getting release history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/releases/{release_name}/notes")
async def get_release_notes(
    request: Request,
    release_name: str,
    revision: int = Query(..., description="The revision number"),
    namespace: str = Query(..., description="The namespace of the release")
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        notes = get_helm_release_notes(release_name, revision, namespace)
        if not notes:
            raise HTTPException(status_code=404, detail="Release notes not found")

        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return {"notes": notes}

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error getting release notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/releases/{release_name}/values/export")
async def export_release_values(
    request: Request,
    release_name: str,
    namespace: str = Query(..., description="The namespace of the release")
):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        file_path = export_helm_release_values_to_file(release_name, namespace)
        if not file_path:
            raise HTTPException(status_code=500, detail="Failed to export release values")

        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return FileResponse(
            file_path,
            filename=f"{release_name}-values.yaml",
            media_type="application/x-yaml"
        )

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error exporting release values: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1

@router.get("/releases/all")
async def list_all_releases(request: Request):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    global IN_PROGRESS
    IN_PROGRESS += 1

    try:
        all_releases = list_all_helm_releases()
        
        global REQUEST_COUNT, REQUEST_LATENCY
        REQUEST_COUNT += 1
        REQUEST_LATENCY += time.time() - start_time
        return all_releases

    except Exception as e:
        global ERROR_COUNT
        ERROR_COUNT += 1
        logger.error(f"Error listing all releases: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        IN_PROGRESS -= 1
