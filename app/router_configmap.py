from fastapi import HTTPException, APIRouter
from kubernetes import client
from starlette.responses import JSONResponse

router = APIRouter()


@router.get("/api/v1/get-all-configmaps-in-cluster")
def get_all_from_cluster_api():
    v1_core_api = client.CoreV1Api()
    configmaps = v1_core_api.list_config_map_for_all_namespaces()
    results = []
    try:
        for configmap in configmaps.items:
            configmap_data = configmap.to_dict()
            configmap_data.pop("metadata", {})
            results.append(configmap_data)
        return {"configmaps": results}
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
