from fastapi import HTTPException, APIRouter
from kubernetes import client

router = APIRouter()


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


