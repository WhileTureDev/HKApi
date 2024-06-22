# controllers/metricsController.py

from fastapi import APIRouter, Request
from prometheus_client import (
    generate_latest, CONTENT_TYPE_LATEST, Counter, Gauge, Histogram
)
from fastapi.responses import Response

router = APIRouter()

# Request metrics
REQUEST_COUNT = Counter('request_count', 'Total number of requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency in seconds', ['method', 'endpoint'])
IN_PROGRESS = Gauge('in_progress_requests', 'In progress requests', ['endpoint'])

# Error metrics
ERROR_COUNT = Counter('error_count', 'Total number of errors', ['method', 'endpoint'])

# Database metrics
DB_QUERY_COUNT = Counter('db_query_count', 'Total number of database queries', ['query'])
DB_QUERY_LATENCY = Histogram('db_query_latency_seconds', 'Database query latency in seconds', ['query'])

# User metrics
USER_CREATION_COUNT = Counter('user_creation_count', 'Total number of users created')
USER_LOGIN_COUNT = Counter('user_login_count', 'Total number of user logins')
USER_LOGIN_FAILURE_COUNT = Counter('user_login_failure_count', 'Total number of failed user logins')

# Deployment metrics
DEPLOYMENT_COUNT = Counter('deployment_count', 'Total number of deployments')
DEPLOYMENT_FAILURE_COUNT = Counter('deployment_failure_count', 'Total number of failed deployments')

# Authentication metrics
AUTH_SUCCESS_COUNT = Counter('auth_success_count', 'Total number of successful authentications')
AUTH_FAILURE_COUNT = Counter('auth_failure_count', 'Total number of failed authentications')

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
