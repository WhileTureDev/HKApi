#!/bin/bash

helm install postgres oci://registry-1.docker.io/bitnamicharts/postgresql -f values.yaml --namespace hkapi