import os
from fastapi import FastAPI, HTTPException
import uvicorn
from kubernetes.client import ApiException
from namespace import create_namespace
from db import create_namespace_record, delete_namespace_record
import subprocess
from kubernetes import config, client

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


@app.post("/deploy")
def deploy(release_name: str, chart_name: str, chart_repo_url: str, provider: str):
    try:
        namespace = create_namespace()
    except Exception as e:
        return e
    if namespace:
        # Deploy the chart
        subprocess.run(["helm", "repo", "add", provider, chart_repo_url])
        subprocess.check_output(
            ["helm", "upgrade", release_name, provider + "/" + chart_name, "--install", "--namespace", namespace])
        create_namespace_record(chart_name, chart_repo_url, namespace)
        status = subprocess.run(["helm", "status", release_name])
        return status


@app.delete("/namespace/{namespace}")
async def delete_namespace(namespace: str):
    k8s_client = client.CoreV1Api()
    try:
        k8s_client.delete_namespace(name=namespace)
        delete_namespace_record(namespace)
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.reason)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
