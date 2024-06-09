#!/bin/bash

IMAGE="steerci/hkui:0.0.2"

docker build -t  ${IMAGE} . --progress=plain
docker push ${IMAGE}

helm del hkui
helm upgrade --install hkui chart/hkui -f chart/hkui/values.yaml

sleep 10

kubectl get pods | grep hkui | grep Running | awk '{print $1}' | xargs kubectl logs -f