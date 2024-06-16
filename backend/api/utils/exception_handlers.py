# utils/exception_handlers.py

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger(__name__)

class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            logger.error(f"HTTPException: {exc.detail}")
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
        except RequestValidationError as exc:
            logger.error(f"Validation error: {exc.errors()}")
            return JSONResponse(
                status_code=422,
                content={"detail": exc.errors()}
            )
        except SQLAlchemyError as exc:
            logger.error(f"Database error: {str(exc)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Database error"}
            )
        except Exception as exc:
            logger.error(f"Unhandled error: {str(exc)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
