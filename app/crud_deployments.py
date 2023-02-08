import yaml
from fastapi import APIRouter, HTTPException, UploadFile
from kubernetes import client
from kubernetes.client import ApiException, V1Namespace

from .db import get_deployments_db

router = APIRouter()


@router.post("/api/v1/create-deployment-by-manifest")
async def create_deployment_by_manifest(file: UploadFile):

    """Create a Kubernetes deployment from a YAML manifest file.

    :parameter file: A file object containing the YAML manifest for the deployment.
    :return: Returns a dictionary with the message key and the value as "Deployment successful" if the deployment was created successfully.
    :raise: HTTPException: If there is an error updating the deployment, raises an exception with status code 500.
    """

    core_v1_api = client.CoreV1Api()
    app_v1_api = client.AppsV1Api()
    yaml_file = file.file
    try:
        docs = yaml.full_load_all(yaml_file)
        for doc in docs:
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
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Deployment successful"}


# Read deployments from a given namespace
@router.get("/api/v1/list-deployments-from-namespace/{namespace}")
def list_deployments_from_given_namespace_api(namespace):
    """
    Get a list of deployments from a specific namespace in the Kubernetes cluster.

    :param namespace: The namespace to retrieve deployments from.
    :type namespace: str

    :return: List of deployment information dictionaries. Each dictionary contains the deployment name, namespace, number of replicas, and the status.
    :rtype: List[Dict[str, Union[str, int]]]
    """
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
    """
    Get a list of deployments from a specific namespace in the Kubernetes cluster.

    :param name:
    :type name: str
    :param namespace: The namespace to retrieve deployments from.
    :type namespace: str

    :return: List of deployment information dictionaries. Each dictionary contains the deployment name, namespace, number of replicas, and the status.
    :rtype: List[Dict[str, Union[str, int]]]
    """
    v1_app_api = client.AppsV1Api()
    deployment = v1_app_api.read_namespaced_deployment(name=name, namespace=namespace)
    result = []
    images = []
    for container in deployment.spec.template.spec.containers:
        images.append(container.image)
    deployment_info = {
        "name": deployment.metadata.name,
        "namespace": deployment.metadata.namespace,
        "image": images,
        "replicas": deployment.spec.replicas,
        "status": deployment.status.replicas
    }
    result.append(deployment_info)
    return result


# Update deployment by manifest yaml
@router.patch("/api/update-deployment-by-manifest/{deployment_name}")
async def update_deployment_by_manifest(file: UploadFile):
    """
    Update a deployment in the Kubernetes cluster by providing a YAML file. The file should contain the updated
    deployment information in the form of a Kubernetes resource manifest.

    :param file: The uploaded YAML file containing the updated deployment information.
    :type file: UploadFile

    :return: A dictionary containing the status of the deployment update. Returns {"message": "Deployment update
    successful"} if the update was successful, otherwise returns {"error": error_message}. :rtype: Dict[str, str]
    """
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


@router.put("/api/v1/edit/{namespace}/deployments/{name}")
async def edit_deployment_api(
        name: str,
        namespace: str,
        replicas: int = None,
        image: str = None
):
    """Edit deployment details

    Endpoint for updating a deployment with specified name and namespace.

    Route: /api/v1/edit/{namespace}/deployments/{name}

    Args:
    name (str): Name of the deployment
    namespace (str): Namespace the deployment belongs to
    replicas (int, optional): Number of replicas for the deployment. Defaults to None.
    image (str, optional): New image for the deployment. Defaults to None.

    Returns:
    dict: A dictionary containing a success message, with key "message".

    Raises:
    HTTPException: If there is an error updating the deployment, raises an exception with status code 500.
    """
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
    """

    Delete a Deployment in a specified namespace.

    The function deletes the Deployment in the specified namespace using the given name. If the operation is
    successful, a message indicating that the Deployment has been successfully deleted is returned. In case of an
    error, an HTTPException with status code 500 and the error detail is raised.

    Parameters:
    name (str): The name of the Deployment to be deleted.
    namespace (str): The namespace in which the Deployment is located.

    Returns: dict: A dictionary with a single key-value pair, where the key is "message" and the value is a string
    indicating that the Deployment was deleted successfully.

    Raises: HTTPException: If there is an error during the deletion process, an HTTPException with status code 500
    and the error detail is raised.

    """

    try:
        v1_app_api = client.AppsV1Api()
        v1_app_api.delete_namespaced_deployment(name=name, namespace=namespace)
        return {"message": f"Deployment {name} successfully deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete deployment by manifest
@router.post("/api/delete-object-by-manifest")
async def delete_deployment_by_manifest(file: UploadFile):
    """
    Delete Kubernetes objects specified in a YAML manifest file.

    This API endpoint allows the user to delete one or multiple Kubernetes objects such as Deployment, Service, ConfigMap, Pod, PersistentVolumeClaim, ResourceQuota and LimitRange by specifying the details in a YAML file. The API accepts a YAML file in the form of a file object, processes it and deletes the specified objects.

    :param file: The YAML file containing the specifications for the Kubernetes objects to be deleted.
    :type file: UploadFile
    :return: A JSON response indicating the result of the operation, including an error message if the operation failed.
    :rtype: Dict[str, str]

    Raises:
    Exception: If the specified "kind" in the YAML file is not supported by this API endpoint.
    """
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
