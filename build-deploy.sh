#!/bin/bash

IMAGE="steerci/hkapi:0.0.1"

docker build -t  ${IMAGE} . --progress=plain
docker push ${IMAGE}

helm del hkapi
helm upgrade --install hkapi helm-hkapi

sleep 4

kubectl get pods | grep hkapi-helm-hkapi | grep Running | awk '{print $1}' | xargs kubectl logs -f