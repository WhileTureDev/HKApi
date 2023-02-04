from fastapi import HTTPException, APIRouter
from kubernetes import client

router = APIRouter()


@router.put("/api/v1/namespaces/{namespace}/deployments/{name}")
async def edit_deployment(
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
