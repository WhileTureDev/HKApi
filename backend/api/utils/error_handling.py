from fastapi import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from kubernetes.client.exceptions import ApiException
import logging

logger = logging.getLogger(__name__)

def handle_general_exception(e: Exception):
    if isinstance(e, HTTPException):
        logger.error(f"HTTPException: {e.detail}")
        raise e
    else:
        logger.error(f"Unhandled exception: {str(e)}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def handle_k8s_exception(e: ApiException):
    if e.status:
        logger.error(f"Kubernetes API exception: {e.reason} (status code: {e.status})")
        raise HTTPException(status_code=e.status, detail=e.reason)
    else:
        logger.error(f"Unhandled Kubernetes API exception: {str(e)}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
