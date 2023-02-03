#!/bin/bash

IMAGE="steerci/hkapi:local"

docker build -t  ${IMAGE} .
docker push ${IMAGE}

helm del hkapi
helm upgrade --install hkapi helm-hkapi