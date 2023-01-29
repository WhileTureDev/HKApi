from fastapi import HTTPException, APIRouter
from src.db import get_all_namespaces

router = APIRouter()


@router.get("/namespaces")
def get_namespaces():
    namespaces = get_all_namespaces()
    if not namespaces:
        raise HTTPException(status_code=204, detail="No namespaces found.")
    return namespaces
