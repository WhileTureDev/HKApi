#!/bin/bash

IMAGE="steerci/hkapi:local"

docker build -t  ${IMAGE} . --progress=plain
docker push ${IMAGE}

helm del hkapi
helm upgrade --install hkapi helm-hkapi