from fastapi import APIRouter, Body
from kubernetes import client

from .db import delete_namespace_record
from pydantic import BaseModel

router = APIRouter()


class NamespacePayload(BaseModel):
    labels: dict


@router.post("/api/v1/create/namespaces")
async def create_namespace(namespace_spec: dict = Body(..., embed=False)):
    try:
        v1_core_api = client.CoreV1Api()
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_spec['metadata']['name']))
        v1_core_api.create_namespace(body=namespace)
        return "Namespace was created "
    except Exception as e:
        return {"message": "Error creating namespace", "details": str(e)}


@router.get("/api/v1/list-all-namespaces")
def get_all_namespaces():
    v1_core_api = client.CoreV1Api()
    namespaces = v1_core_api.list_namespace().items
    namespaces_info = []
    for namespace in namespaces:
        namespaces_info.append({
            "name": namespace.metadata.name,
            "status": namespace.status.phase
        })
    return {"namespaces": namespaces_info}


@router.patch("/api/v1/update-namespace/{namespace_name}")
async def update_namespace(namespace_name: str, payload: NamespacePayload):
    v1_core_api = client.CoreV1Api()
    namespace = v1_core_api.read_namespace(name=namespace_name)
    namespace.metadata.labels.update(payload.labels)
    namespace = v1_core_api.patch_namespace(name=namespace_name, body=namespace)
    return {"message": "Namespace updated successfully", "namespace": namespace.to_dict()}


@router.delete("/api/v1/namespace/{namespace}")
async def delete_namespace_api(namespace: str):
    k8s_client = client.CoreV1Api()
    try:
        k8s_client.delete_namespace(name=namespace)
        delete_namespace_record(namespace)
        return f"Namespace {namespace} was deleted"
    except Exception as e:
        return e

# @router.delete("/api/v1/namespaces/all")
# def delete_all_namespaces_from_cluster_api():
#     try:
#         namespaces = get_all_namespaces_from_db()
#         if not namespaces:
#             raise HTTPException(status_code=404, detail="No namespaces found in the database.")
#         for namespace in namespaces:
#             delete_namespace_from_cluster(namespace)
#         delete_all_namespaces_from_db()
#     except Exception as e:
#         return e
#     return {"message": f"Namespaces {namespaces} have been deleted."}
