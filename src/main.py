import os
import uvicorn
from fastapi import FastAPI
from kubernetes import config
import routers.deploy as _deploy
import routers.get_namespaces as _get_namespaces
import routers.delete_namespace as _delete_namespace
import routers.get_cluster_summary as _get_cluster_summary
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

if __name__ == "__main__":
    app.include_router(_deploy.router)
    app.include_router(_get_namespaces.router)
    app.include_router(_delete_namespace.router)
    app.include_router(_get_cluster_summary.router)
    uvicorn.run(app, host="0.0.0.0", port=8000)
