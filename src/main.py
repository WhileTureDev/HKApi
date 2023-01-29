import os
import subprocess

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from kubernetes import config, client
import json

from starlette.responses import JSONResponse

from db import create_namespace_record, delete_namespace_record, get_all_namespaces, delete_all_namespaces_from_db, \
    get_all_namespaces_from_db
from namespace import create_namespace, check_if_namespace_exist, delete_namespace_from_cluster

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


@app.get("/namespaces")
def get_namespaces():
    namespaces = get_all_namespaces()
    if not namespaces:
        raise HTTPException(status_code=204, detail="No namespaces found.")
    return namespaces


@app.post("/deploy")
async def deploy(request: Request):
    status = []
    try:
        # Get the data from the request body in JSON format
        data = await request.json()

        # Iterate through the list of charts in the data
        for chart in data['charts']:
            chart_name = chart.get("chart_name")
            chart_repo_url = chart.get("chart_repo_url")
            release_name = chart.get("release_name")
            provider = chart.get("provider")
            namespace = chart.get("namespace")

            # Check if the helm repo exists
            repo_output = subprocess.run(["helm", "repo", "list"], capture_output=True)
            if str(provider) in repo_output.stdout.decode():
                print(f"{provider} already exists")
            else:
                subprocess.run(["helm", "repo", "add", provider, chart_repo_url])
                print(f"{provider} added")

            # Check if the namespace exists, create it if it doesn't
            if not check_if_namespace_exist(namespace):
                create_namespace(namespace)
                # Upgrade or install the chart in the namespace
            subprocess.run(
                ["helm", "upgrade", "--install", release_name, provider + "/" + chart_name, "--namespace",
                 namespace],
                capture_output=True)
            # Update the database with the new chart information
            create_namespace_record(chart_name, chart_repo_url, namespace)
            release_status = subprocess.run(["helm", "status", release_name, "--namespace", namespace],
                                            capture_output=True)
            status.append({
                "chart_name": chart_name,
                "chart_repo_url": chart_repo_url,
                "release_name": release_name,
                "provider": provider,
                "namespace": namespace,
                "repo_output": repo_output.stdout.decode(),
                "release_status": release_status.stdout.decode()
            })
    except subprocess.CalledProcessError as e:
        status.append(e.stderr)
    return JSONResponse(status, status_code=200)


@app.delete("/namespace/{namespace}")
async def delete_namespace(namespace: str):
    k8s_client = client.CoreV1Api()
    status = []
    try:
        k8s_client.delete_namespace(name=namespace)
        status = delete_namespace_record(namespace)
    except Exception as e:
        status.append(e)
    return status


@app.delete("/namespaces/all")
def delete_all_namespaces():
    try:
        namespaces = get_all_namespaces_from_db()
        if not namespaces:
            raise HTTPException(status_code=404, detail="No namespaces found in the database.")
        for namespace in namespaces:
            delete_namespace_from_cluster(namespace)
        delete_all_namespaces_from_db()
    except Exception as e:
        return e
    return {"message": "All namespaces have been deleted."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
