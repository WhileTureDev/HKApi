from fastapi import APIRouter, HTTPException, Depends
from .crud_user import get_current_active_user

from .db import get_deployments_db

router = APIRouter()


# Read all deployments from database
@router.get("/api/v1/list-db-deployments", dependencies=[Depends(get_current_active_user)])
def get_deployments_from_database_api():
    """
    Get the deployments from the database.

    Returns:
        JSON response containing the list of deployments.

    Raises: HTTPException: with status code 204 if no deployments found in the database, and with status code 500 in
    case of any unexpected error.
    """

    deployments = get_deployments_db()
    if not deployments:
        raise HTTPException(status_code=204, detail="No namespaces found.")
    return deployments
