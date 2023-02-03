#!/bin/bash

IMAGE="steerci/hkapi"

docker build -t  ${IMAGE} .
docker push ${IMAGE}

helm del hkapi
helm upgrade --install hkapi helm-hkapi