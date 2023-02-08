from typing import Dict
from fastapi import HTTPException, APIRouter
from kubernetes import client

router = APIRouter()


# Create config map
@router.post("/api/v1/namespaces/{namespace}/configmaps")
def create_configmap_in_given_namespace_api(
        namespace: str,
        name: str,
        data: Dict[str, str]
):

    """

    Create a ConfigMap in a given namespace.

    Parameters:
    namespace (str): The namespace where the ConfigMap will be created.
    name (str): The name of the ConfigMap to be created.
    data (Dict[str, str]): The data to be stored:8 in the ConfigMap.

    Returns: list: A list of dictionaries containing information about the created ConfigMap, including its `name`,
    `namespace`, `data`, and `creationTimestamp`.

    Raises: HTTPException: If there is an error creating the ConfigMap. The exception will include a status code of
    500 and the error details.

    """

    try:
        # Create the ConfigMap object
        configmap = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=namespace
            ),
            data=data
        )

        # Create the ConfigMap
        v1_core_api = client.CoreV1Api()
        v1_core_api.create_namespaced_config_map(
            namespace=namespace,
            body=configmap
        )
        results = []
        configmap = v1_core_api.read_namespaced_config_map(name=name, namespace=namespace)
        configmap_info = {
            "name": configmap.metadata.name,
            "namespace": configmap.metadata.namespace,
            "data": configmap.data,
            "creationTimestamp": configmap.metadata.creationTimestamp
        }
        results.append(configmap_info)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Read configmaps from a given namespace
@router.get("/api/v1/list-configmaps/{namespace}")
def list_configmap_from_given_namespace_api(namespace: str):
    """
    List all ConfigMaps in a given namespace.
    :param namespace:
    :return: dict: A dictionary containing all ConfigMaps in the namespace. The dictionary has a key "configmap" that maps to a list of dictionaries, where each dictionary represents a ConfigMap and has keys "name", "namespace", and "data".
    :raise: HTTPException: If an error occurs while listing the ConfigMaps, this exception is raised with a status code of 500 and detail message.
    """

    v1_core_api = client.CoreV1Api()

    try:
        results = []
        configmaps = v1_core_api.list_namespaced_config_map(namespace=namespace)
        for configmap in configmaps.items:
            configmap_info = {
                "name": configmap.metadata.name,
                "namespace": configmap.metadata.namespace,
                "data": configmap.data
            }
            results.append(configmap_info)
        return {"configmap": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Read configmap form a namespace
@router.get("/api/v1/get/{namespace}/configmap/{name}")
def get_configmap_from_given_namespace_api(name: str, namespace: str):

    """

    Get ConfigMap from a given namespace in the cluster.

    :param name: the name of the ConfigMap.
    :type name: str
    :param namespace: the name of the namespace.
    :type namespace: str
    :return: a dictionary containing the ConfigMap information with keys: name, namespace, and data.
    :rtype: Dict[str, Union[str, Dict[str, str]]]
    :raises HTTPException: if there was an error accessing the ConfigMap.

    """

    v1_core_api = client.CoreV1Api()

    try:
        results = []
        configmap = v1_core_api.read_namespaced_config_map(name=name, namespace=namespace)
        configmap_info = {
            "name": configmap.metadata.name,
            "namespace": configmap.metadata.namespace,
            "data": configmap.data
        }
        results.append(configmap_info)
        return {"configmap": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Update configmap
@router.put("/api/v1/edit/{namespace}/configmaps/{name}")
async def edit_config_map_api(
        name: str,
        namespace: str,
        data: dict = None
):
    """

    Create or edit a ConfigMap in a given namespace

    :param name: The name of the ConfigMap to create or edit
    :param namespace: The namespace where the ConfigMap belongs
    :param data: The data to store in the ConfigMap. This is an optional parameter.
    :return: A JSON response indicating that the ConfigMap has been updated successfully.
    :raises HTTPException: If there was an error during the update process.

    """

    try:
        # Get the ConfigMap
        core_v1_api = client.CoreV1Api()
        config_map = core_v1_api.read_namespaced_config_map(name=name, namespace=namespace)

        # Edit the ConfigMap
        if data:
            config_map.data = data

        # Update the ConfigMap
        core_v1_api.patch_namespaced_config_map(
            name=name,
            namespace=namespace,
            body=config_map
        )

        return {"message": f"ConfigMap '{name}' updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/v1/delete/{namespace}/configmap/{name}")
async def delete_configmap_from_given_namespace(
        name: str,
        namespace: str
):
    """

    Delete a ConfigMap from a given namespace.

    Args:
    - name (str): The name of the ConfigMap to delete.
    - namespace (str): The name of the namespace where the ConfigMap is located.

    Returns:
    - A JSON response containing the message "ConfigMap {name} successfully deleted from namespace {namespace}"

    Raises: - HTTPException: If there is an error in deleting the ConfigMap, an HTTPException with a status code of
    500 and detail of the error message is raised.

    """

    try:
        v1_core_api = client.CoreV1Api()
        v1_core_api.delete_namespaced_config_map(name=name, namespace=namespace)
        return {"message": f"ConfigMap {name} successfully deleted form namespace  {namespace}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
