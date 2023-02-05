import os

from fastapi import FastAPI
from kubernetes import config
from app import crud_deployments, crud_namespace, router_cluster_summary, router_pods, crud_services, \
                 crud_helm, crud_configmap, crud_secretes, crud_database, monitoring

app = FastAPI()
cluster_config = os.getenv('cluster_config')

# Authenticate against kubernetes cluster
if cluster_config == 'out-of-cluster':
    try:
        config.load_kube_config()
        print("using out-of-cluster K8s conf")
    except Exception as e:
        print("Error loading out of cluster k8s config: {0}".format(e))

else:
    try:
        config.load_incluster_config()
        print("using in-cluster K8s conf")
    except Exception as e:
        print("Error loading in-cluster k8s config: {0}".format(e))

# Include routers
app.include_router(crud_helm.router)
app.include_router(crud_deployments.router)
app.include_router(crud_namespace.router)
app.include_router(router_pods.router)
app.include_router(crud_services.router)
app.include_router(crud_configmap.router)
app.include_router(crud_secretes.router)
app.include_router(router_cluster_summary.router)
app.include_router(crud_database.router)
app.include_router(monitoring.router)
