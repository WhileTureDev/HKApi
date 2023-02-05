import yaml
from fastapi import APIRouter, HTTPException, UploadFile
from kubernetes import client
from kubernetes.client import ApiException, V1Namespace

from .db import get_deployments_db

router = APIRouter()


# @router.get("/api/v1/list-all-deployments")
# def get_all_deployments_from_cluster_api():
#     k8s_client = client.AppsV1Api()
#     deployments = k8s_client.list_deployment_for_all_namespaces(watch=False)
#     results = []
#     for deployment in deployments.items:
#         deployment_info = {
#             "name": deployment.metadata.name,
#             "namespace": deployment.metadata.namespace,
#             "replicas": deployment.spec.replicas,
#             "status": deployment.status.replicas,
#         }
#         results.append(deployment_info)
#     return results

# Create deployment by manifest yaml
@router.post("/api/v1/create-deployment-by-manifest")
async def create_deployment_by_manifest(file: UploadFile):
    core_v1_api = client.CoreV1Api()
    app_v1_api = client.AppsV1Api()
    yaml_file = file.file
    try:
        docs = yaml.full_load_all(yaml_file)
        for doc in docs:
            # api_version = doc["apiVersion"]
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


# Read deployments from a given namespace
@router.get("/api/v1/list-deployments-from-namespace/{namespace}")
def list_deployments_from_given_namespace_api(namespace):
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


# Read deployment from a given namespace
@router.get("/api/v1/list-deployment/{namespace}/deployment/{name}")
def get_deployment_from_a_given_namespace_api(
        name: str,
        namespace: str
):
    v1_app_api = client.AppsV1Api()
    deployment = v1_app_api.read_namespaced_deployment(name=name, namespace=namespace)
    result = []
    deployment_info = {
        "name": deployment.metadata.name,
        "namespace": deployment.metadata.namespace,
        "replicas": deployment.spec.replicas,
        "status": deployment.status.replicas
    }
    result.append(deployment_info)
    return result


# Update deployment by manifest yaml
@router.patch("/api/update-deployment-by-manifest/{deployment_name}")
async def update_deployment_by_manifest(file: UploadFile):
    core_v1_api = client.CoreV1Api()
    app_v1_api = client.AppsV1Api()
    yaml_file = file.file
    try:
        docs = yaml.full_load_all(yaml_file)
        for doc in docs:
            # api_version = doc["apiVersion"]
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
                core_v1_api.patch_namespaced_pod(name=pod_name, namespace=namespace, body=doc)
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


# Update/Edit deployment
@router.put("/api/v1/edit/{namespace}/deployments/{name}")
async def edit_deployment_api(
        name: str,
        namespace: str,
        replicas: int = None,
        image: str = None
):
    try:
        # Get the Deployment
        app_v1_api = client.AppsV1Api()
        deployment = app_v1_api.read_namespaced_deployment(name=name, namespace=namespace)

        # Edit the Deployment
        if replicas:
            deployment.spec.replicas = replicas
        if image:
            deployment.spec.template.spec.containers[0].image = image

        # Update the Deployment
        app_v1_api.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=deployment
        )

        return {"message": f"Deployment '{name}' updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete deployment
@router.delete("/api/v1/delete/{namespace}/deployments/{name}")
async def delete_deployment_api(
        name: str,
        namespace: str,
):
    try:
        v1_app_api = client.AppsV1Api()
        v1_app_api.delete_namespaced_deployment(name=name, namespace=namespace)
        return {"message": f"Deployment {name} successfully deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete deployment by manifest
@router.post("/api/delete-deployment-by-manifest")
async def delete_deployment_by_manifest(file: UploadFile):
    core_v1_api = client.CoreV1Api()
    app_v1_api = client.AppsV1Api()
    yaml_file = file.file
    try:
        docs = yaml.full_load_all(yaml_file)
        for doc in docs:
            # api_version = doc["apiVersion"]
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
