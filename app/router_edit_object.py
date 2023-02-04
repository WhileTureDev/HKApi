from fastapi import HTTPException, APIRouter
from kubernetes import client

router = APIRouter()


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


@router.put("/api/v1/edit/{namespace}/secrets/{name}")
async def edit_secret_api(
        name: str,
        namespace: str,
        data: dict = None
):
    try:
        # Get the Secret
        core_v1_api = client.CoreV1Api()
        secret = core_v1_api.read_namespaced_secret(name=name, namespace=namespace)

        # Edit the Secret
        if data:
            secret.data = data

        # Update the Secret
        core_v1_api.patch_namespaced_secret(
            name=name,
            namespace=namespace,
            body=secret
        )

        return {"message": f"Secret '{name}' updated successfully"}
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
