import os
import subprocess

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from kubernetes import config, client
from kubernetes.client import ApiException

from db import create_namespace_record, delete_namespace_record, get_all_namespaces
from namespace import create_namespace, check_if_namespace_exist


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
async def deploy(request: Request):
    # Create namespace

    # Deploy the chart
    global status
    data = await request.json()
    for chart in data['charts']:
        chart_name = chart.get("chart_name")
        chart_repo_url = chart.get("chart_repo_url")
        release_name = chart.get("release_name")
        provider = chart.get("provider")
        namespace = chart.get("namespace")
        repo_output = subprocess.run(["helm", "repo", "list"], capture_output=True)

        # Check if helm  repo dose not exists
        if str(provider) in repo_output.stdout.decode():
            print(f"{provider} already exists")
        else:
            subprocess.run(["helm", "repo", "add", provider, chart_repo_url])
            print(f"{provider} added")

        if not check_if_namespace_exist(namespace):
            create_namespace(namespace)
        subprocess.check_output(
            ["helm", "upgrade", "--install", release_name, provider + "/" + chart_name, "--namespace", namespace])
        # Update database
        create_namespace_record(chart_name, chart_repo_url, namespace)
        status = subprocess.run(["helm", "status", release_name, "--namespace", namespace ])
    return status


@app.delete("/namespace/{namespace}")
async def delete_namespace(namespace: str):
    k8s_client = client.CoreV1Api()
    try:
        k8s_client.delete_namespace(name=namespace)
        delete_namespace_record(namespace)
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.reason)


@app.get("/namespaces")
def get_namespaces():
    namespaces = get_all_namespaces()
    if not namespaces:
        raise HTTPException(status_code=204, detail="No namespaces found.")
    return namespaces


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
