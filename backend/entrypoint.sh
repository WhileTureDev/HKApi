#!/bin/bash

NAMESPACE="hkapi"

# Read postgres password and export it
POSTGRES_PASSWORD=$(kubectl get secret --namespace "${NAMESPACE}" postgres-postgresql -o jsonpath="{.data.postgres-password}" | base64 -d)
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
echo "Database password is ${POSTGRES_PASSWORD}"


# Start uvicorn server

uvicorn main:app --proxy-headers --host 0.0.0.0 --port 80  --log-level info  --workers 4