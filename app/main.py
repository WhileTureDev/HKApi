import os

from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from kubernetes import config
from starlette.staticfiles import StaticFiles

from app import crud_deployments, crud_namespace, router_cluster_summary, router_pods, rd_services, \
    crud_helm, crud_configmap, crud_secretes, crud_database, monitoring, r_nodes, crd_ingress, crud_user

app = FastAPI()
cluster_config = os.getenv('cluster_config')

"""
Authenticate against the Kubernetes cluster based on the cluster_config flag.
If cluster_config is set to out-of-cluster, the function will try to load the configuration from the kubeconfig file.
If the configuration is loaded successfully, the function will print "using out-of-cluster K8s conf".
If cluster_config is not set to out-of-cluster, the function will try to load the configuration as an in-cluster config.
If the configuration is loaded successfully, the function will print "using in-cluster K8s conf".
If there is an error loading the configuration, the function will print an error message with the specific error.
"""
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

"""
Include all the routers in the FastAPI application

The following routers are included in the application:

crud_helm
crud_deployments
crud_namespace
router_pods
rd_services
crud_configmap
crud_secretes
router_cluster_summary
crud_database
monitoring
r_nodes
crd_ingress
"""
app.include_router(crud_user.router)
app.include_router(crud_helm.router)
app.include_router(crud_deployments.router)
app.include_router(crud_namespace.router)
app.include_router(router_pods.router)
app.include_router(rd_services.router)
app.include_router(crud_configmap.router)
app.include_router(crud_secretes.router)
app.include_router(router_cluster_summary.router)
app.include_router(crud_database.router)
app.include_router(monitoring.router)
app.include_router(r_nodes.router)
app.include_router(crd_ingress.router)
app.mount("/", StaticFiles(directory="html", html=True), name="wiki")
