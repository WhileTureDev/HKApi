# controllers/adminControllers/adminHelmController.py

import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.deploymentModel import Deployment as DeploymentModel
from utils.database import get_db
from utils.auth import get_current_active_user, get_current_user_roles, is_admin
from models.userModel import User as UserModel
from typing import List

router = APIRouter()
logger = logging.getLogger(__name__)

def deployment_to_dict(deployment: DeploymentModel) -> dict:
    return {
        "id": deployment.id,
        "project": deployment.project,
        "install_type": deployment.install_type,
        "release_name": deployment.release_name,
        "chart_name": deployment.chart_name,
        "chart_repo_url": deployment.chart_repo_url,
        "namespace_id": deployment.namespace_id,
        "namespace_name": deployment.namespace_name,
        "values": deployment.values,
        "revision": deployment.revision,
        "active": deployment.active,
        "status": deployment.status,
        "created_at": deployment.created_at,
        "updated_at": deployment.updated_at,
        "owner_id": deployment.owner_id
    }

@router.get("/admin/helm/releases/all", response_model=List[dict])
async def list_all_releases(
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user),
        current_user_roles: List[str] = Depends(get_current_user_roles)
):
    logger.info("Listing all releases across all namespaces")

    try:
        if not is_admin(current_user_roles):
            logger.warning(f"User {current_user.username} attempted to access admin-only endpoint")
            raise HTTPException(status_code=403, detail="Not authorized")

        releases = db.query(DeploymentModel).all()
        if not releases:
            logger.warning("No releases found")
            raise HTTPException(status_code=404, detail="No releases found")

        return [deployment_to_dict(deployment) for deployment in releases]

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"An error occurred while listing releases: {str(e)}")
        raise HTTPException(status_code=500, detail="An internal error occurred")
