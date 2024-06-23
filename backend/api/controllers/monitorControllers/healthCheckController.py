import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.database import get_db
from utils.circuit_breaker import call_database_operation
from controllers.monitorControllers.metricsController import (
    REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)
import time

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", response_model=dict)
async def health_check(db: Session = Depends(get_db)):
    start_time = time.time()
    endpoint = "/health"
    method = "GET"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        # Perform a simple query to check the database connection
        call_database_operation(lambda: db.execute(text("SELECT 1")))
        logger.info("Health check passed")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="Health check failed")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()
