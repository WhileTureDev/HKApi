# utils/error_handling.py

import logging
from fastapi import HTTPException
from kubernetes.client import ApiException

logger = logging.getLogger(__name__)

def handle_k8s_exception(e: ApiException):
    if e.status:
        logger.error(f"Kubernetes API exception: {e.reason}")
        raise HTTPException(status_code=e.status, detail=e.reason)
    else:
        logger.error(f"Unhandled Kubernetes API exception: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

def handle_general_exception(e: Exception):
    if isinstance(e, HTTPException):
        raise e
    else:
        logger.error(f"Unhandled exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
