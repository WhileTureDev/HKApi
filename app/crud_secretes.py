import base64
from typing import Dict
from fastapi import HTTPException, APIRouter
from kubernetes import client

router = APIRouter()


# Create secret
@router.post("/api/v1/secrets/{namespace}/secrets/{name}")
async def create_secret_api(
        namespace: str,
        name: str,
        data: Dict[str, str]
):
    # Encode the secret data to base64
    encoded_data = {}
    for key, value in data.items():
        encoded_data[key] = base64.b64encode(value.encode()).decode()
    secret = client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        data=encoded_data
    )
    try:
        v1_core_api = client.CoreV1Api()
        v1_core_api.create_namespaced_secret(namespace=namespace, body=secret)
        results = []
        secret = v1_core_api.read_namespaced_secret(name=name, namespace=namespace)
        secret_info = {
            "name": secret.metadata.name,
            "namespace": secret.metadata.namespace,
            "data": secret.data
        }
        results.append(secret_info)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get secrets from a given namespace
@router.get("/api/v1/list-secrets/{namespace}")
def list_secrets_from_given_namespace_api(
        namespace: str
):
    v1_core_api = client.CoreV1Api()

    try:
        results = []
        secrets = v1_core_api.list_namespaced_secret(namespace=namespace)
        for secret in secrets.items:
            secret_info = {
                "name": secret.metadata.name,
                "namespace": secret.metadata.namespace,
                "data": secret.data
            }
            results.append(secret_info)
        return {"secret": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Read secret from a given namespace
@router.get("/api/v1/get/{namespace}/secret/{name}")
def get_secret_from_given_namespace_api(
        name: str,
        namespace: str
):
    v1_core_api = client.CoreV1Api()

    try:
        results = []
        secret = v1_core_api.read_namespaced_secret(name=name, namespace=namespace)
        secret_info = {
            "name": secret.metadata.name,
            "namespace": secret.metadata.namespace,
            "data": secret.data
        }
        results.append(secret_info)
        return {"secret": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Update config map
@router.put("/api/v1/edit/{namespace}/secret/{name}")
async def edit_secret_in_the_given_namespace_api(
        name: str,
        namespace: str,
        data: Dict[str, str] = None
):
    try:
        # Get the Secret
        v1_core_api = client.CoreV1Api()
        secret = v1_core_api.read_namespaced_secret(name=name, namespace=namespace)

        # Edit the Secret
        if data:
            secret.data = {k: base64.b64encode(v.encode()).decode() for k, v in data.items()}

        # Update the Secret
        v1_core_api.patch_namespaced_secret(
            name=name,
            namespace=namespace,
            body=secret
        )
        results = []
        secret_info = {
            "name": secret.metadata.name,
            "namespace": secret.metadata.namespace,
            "data": secret.data
        }
        results.append(secret_info)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/v1/delete/{namespace}/secret/{name}")
async def delete_secret_from_given_namespace(
        name: str,
        namespace: str
):
    try:
        v1_core_api = client.CoreV1Api()
        v1_core_api.delete_namespaced_secret(name=name, namespace=namespace)
        return {"message": f"Secret {name} successfully deleted form namespace  {namespace}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
