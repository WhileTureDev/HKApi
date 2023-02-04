from typing import Dict
from fastapi import HTTPException, APIRouter
from kubernetes import client

router = APIRouter()


@router.post("/api/v1/namespaces/{namespace}/configmaps")
def create_configmap_in_given_namespace_api(
        namespace: str,
        name: str,
        data: Dict[str, str]
):
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


@router.get("/api/v1/get-all-configmaps-in-cluster")
def get_all_from_cluster_api():
    v1_core_api = client.CoreV1Api()
    configmaps = v1_core_api.list_config_map_for_all_namespaces()
    results = []
    try:
        for configmap in configmaps.items:
            configmap_info = {
                "name": configmap.metadata.name,
                "namespace": configmap.metadata.namespace,
                "data": configmap.data
            }
            results.append(configmap_info)
        return {"configmaps": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/get-{namespace}/configmap{name}")
def get_configmap_from_given_namespace_api(
        name: str,
        namespace: str
):
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


@router.get("/api/v1/list-configmaps/{namespace}")
def list_configmap_from_given_namespace_api(
        namespace: str
):
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


@router.put("/api/v1/edit/{namespace}/configmaps/{name}")
async def edit_config_map_api(
        name: str,
        namespace: str,
        data: dict = None
):
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
    try:
        v1_core_api = client.CoreV1Api()
        v1_core_api.delete_namespaced_config_map(name=name, namespace=namespace)
        return {"message": f"ConfigMap {name} successfully deleted form namespace  {namespace}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
