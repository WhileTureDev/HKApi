#!/bin/bash

export POSTGRES_PASSWORD=$(kubectl get secret --namespace default postgres-postgresql -o jsonpath="{.data.postgres-password}" | base64 -d)
kubectl port-forward svc/postgres-postgresql  5432:5432 -n default &
make html
PID=$( ps -ef | grep port-forward |grep -v "grep"| awk '{print $2}')

kill -9 "${PID}"