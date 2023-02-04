import subprocess

import yaml
from fastapi import Request, APIRouter, HTTPException, UploadFile
from kubernetes import client
from kubernetes.client import ApiException, V1Namespace
from starlette.responses import JSONResponse

from .db import create_namespace_record, get_deployments_db
from .def_namespace import create_namespace, check_if_namespace_exist

router = APIRouter()


# Read all deployments from database
@router.get("/api/list-db-deployments")
def get_deployments_db_api():
    deployments = get_deployments_db()
    if not deployments:
        raise HTTPException(status_code=204, detail="No namespaces found.")
    return deployments


@router.get("/api/list-all-deployments")
def get_all_deployments_api():
    k8s_client = client.AppsV1Api()
    deployments = k8s_client.list_deployment_for_all_namespaces(watch=False)
    results = []
    for deployment in deployments.items:
        deployment_info = {
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "replicas": deployment.spec.replicas,
            "status": deployment.status.replicas,
        }
        results.append(deployment_info)
    return results


@router.get("/api/list-deployments-by-namespace/{namespace}")
def get_deployments_api(namespace):
    k8s_client = client.AppsV1Api()
    deployments = k8s_client.list_namespaced_deployment(namespace)
    results = []
    for deployment in deployments.items:
        deployment_info = {
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "replicas": deployment.spec.replicas,
            "status": deployment.status.replicas,
        }
        results.append(deployment_info)
    return results


@router.post("/create-helm-releaset")
async def create_helm_release_api(request: Request):
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

            release_status = subprocess.run(["helm", "status", release_name, "--namespace", namespace],
                                            capture_output=True)
            create_namespace_record(chart_name, chart_repo_url, namespace)
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


@router.post("/api/create-deployment-by-manifest")
async def create_deployment_by_manifest(file: UploadFile):
    core_v1_api = client.CoreV1Api()
    app_v1_api = client.AppsV1Api()
    yaml_file = file.file
    try:
        docs = yaml.full_load_all(yaml_file)
        for doc in docs:
            api_version = doc["apiVersion"]
            kind = doc["kind"]
            namespace = doc.get("metadata", {}).get("namespace")
            if namespace:
                try:
                    core_v1_api.read_namespace(namespace)
                except ApiException as e:
                    if e.status != 404:
                        raise
                    core_v1_api.create_namespace(V1Namespace(metadata={"name": namespace}))
            if kind == "Service":
                core_v1_api.create_namespaced_service(namespace, doc)
            elif kind == "Deployment":
                app_v1_api.create_namespaced_deployment(namespace, doc)
            elif kind == "ConfigMap":
                core_v1_api.create_namespaced_config_map(namespace, doc)
            elif kind == "Pod":
                core_v1_api.create_namespaced_pod(namespace, doc)
            elif kind == "PersistentVolumeClaim":
                core_v1_api.create_namespaced_persistent_volume_claim(namespace, doc)
            elif kind == "Secret":
                core_v1_api.create_namespaced_secret(namespace, doc)
            elif kind == "PersistentVolume":
                core_v1_api.create_persistent_volume(doc)
            elif kind == "ResourceQuota":
                core_v1_api.create_namespaced_resource_quota(namespace, doc)
            elif kind == "LimitRange":
                core_v1_api.create_namespaced_limit_range(namespace, doc)
            else:
                raise Exception(f"Unsupported kind: {kind}")
    except Exception as e:
        return {"error": str(e)}
    return {"message": "Deployment successful"}


@router.post("/api/delete-deployment-by-manifest")
async def delete_deployment_by_manifest(file: UploadFile):
    core_v1_api = client.CoreV1Api()
    app_v1_api = client.AppsV1Api()
    yaml_file = file.file
    try:
        docs = yaml.full_load_all(yaml_file)
        for doc in docs:
            api_version = doc["apiVersion"]
            kind = doc["kind"]
            name = doc["metadata"]["name"]
            namespace = doc["metadata"].get("namespace")
            if kind == "Service":
                core_v1_api.delete_namespaced_service(name, namespace, body={})
            elif kind == "Deployment":
                app_v1_api.delete_namespaced_deployment(name, namespace, body={})
            elif kind == "ConfigMap":
                core_v1_api.delete_namespaced_config_map(name, namespace, body={})
            elif kind == "Pod":
                core_v1_api.delete_namespaced_pod(name, namespace, body={})
            elif kind == "PersistentVolumeClaim":
                core_v1_api.delete_namespaced_persistent_volume_claim(name, namespace, body={})
            elif kind == "ResourceQuota":
                core_v1_api.delete_namespaced_resource_quota(name, namespace, body={})
            elif kind == "LimitRange":
                core_v1_api.delete_namespaced_limit_range(name, namespace, body={})
            else:
                raise Exception(f"Unsupported kind: {kind}")
    except Exception as e:
        return {"error": str(e)}
    return {"message": "Deletion successful"}


@router.patch("/api/update-deployment-by-manifest/{deployment_name}")
async def update_deployment_by_manifest(file: UploadFile):
    core_v1_api = client.CoreV1Api()
    app_v1_api = client.AppsV1Api()
    yaml_file = file.file
    try:
        docs = yaml.full_load_all(yaml_file)
        for doc in docs:
            api_version = doc["apiVersion"]
            kind = doc["kind"]
            namespace = doc.get("metadata", {}).get("namespace")
            if namespace:
                try:
                    core_v1_api.read_namespace(namespace)
                except ApiException as e:
                    if e.status == 404:
                        return {"error": f"Namespace {namespace} not found"}
            if kind == "Service":
                service_name = doc["metadata"]["name"]
                core_v1_api.patch_namespaced_service(name=service_name, namespace=namespace, body=doc)
            elif kind == "Deployment":
                deployment_name = doc["metadata"]["name"]
                app_v1_api.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=doc)
            elif kind == "ConfigMap":
                config_name = doc["metadata"]["name"]
                core_v1_api.patch_namespaced_config_map(name=config_name, namespace=namespace, body=doc)
            elif kind == "Pod":
                pod_name = doc["metadata"]["name"]
                core_v1_api.patch_namespaced_pod(pod_name=pod_name, namespace=namespace, body=doc)
            elif kind == "PersistentVolumeClaim":
                claim_name = doc["metadata"]["name"]
                core_v1_api.patch_namespaced_persistent_volume_claim(name=claim_name, namespace=namespace, body=doc)
            elif kind == "Secret":
                secret_name = doc["metadata"]["name"]
                core_v1_api.patch_namespaced_secret(name=secret_name, namespace=namespace, body=doc)
            elif kind == "PersistentVolume":
                volume_name = doc["metadata"]["name"]
                core_v1_api.patch_persistent_volume(name=volume_name, namespace=namespace, body=doc)
            elif kind == "ResourceQuota":
                name_quota = doc["metadata"]["name"]
                core_v1_api.patch_namespaced_resource_quota(name=name_quota, namespace=namespace, body=doc)
            elif kind == "LimitRange":
                name_limit_range = doc["metadata"]["name"]
                core_v1_api.patch_namespaced_limit_range(name=name_limit_range, namespace=namespace, body=doc)
            else:
                raise Exception(f"Unsupported kind: {kind}")
    except Exception as e:
        return {"error": str(e)}
    return {"message": "Deployment update successful"}
