from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Body
from kubernetes import client
from kubernetes.client import V1Ingress
from pydantic import BaseModel

router = APIRouter()


@router.get("/api/v1/namespaces/{namespace_name}/ingresses")
async def list_ingresses_by_namespace(namespace_name: str):
    try:
        api_instance = client.NetworkingV1Api()
        ingresses = api_instance.list_namespaced_ingress(namespace=namespace_name)
        results = []
        for ingress in ingresses.items:
            ingress_info = {
                "name": ingress.metadata.name,
                "namespace": ingress.metadata.namespace,
                "rules": [
                    {
                        "host": rule.host,
                        "paths": [
                            {
                                "path": path.path,
                                "service_name": path.backend.service.name
                            } for path in rule.http.paths
                        ]
                    } for rule in ingress.spec.rules
                ]
            }
            results.append(ingress_info)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/create/ingresses")
async def create_ingress(ingress_spec: dict = Body(..., embed=False)):
    try:
        networking_v1_api = client.NetworkingV1Api()
        ingress = client.V1Ingress(metadata=client.V1ObjectMeta(name=ingress_spec['metadata']['name']),
                                   spec=ingress_spec['spec'])
        networking_v1_api.create_namespaced_ingress(namespace=ingress_spec['metadata']['namespace'],
                                                    body=ingress)
        return {"message": "Ingress was created"}
    except Exception as e:
        return {"message": "Error creating ingress", "details": str(e)}


class UpdateIngressResponse(BaseModel):
    name: str
    namespace: str
    rules: List[Dict[str, Any]]


# @router.patch("/api/v1/update/namespaces/{namespace_name}/ingresses/{ingress_name}")
# async def update_ingress(namespace_name: str, ingress_name: str, ingress_spec: Dict[str, Any]):
#     try:
#         api_instance = client.NetworkingV1Api()
#         body = client.V1Ingress(metadata=client.V1ObjectMeta(name=ingress_name), spec=ingress_spec)
#         api_instance.patch_namespaced_ingress(name=ingress_name, namespace=namespace_name, body=body)
#         return "Ingress was patched"
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/v1/delete/namespaces/{namespace_name}/ingresses/{ingress_name}")
def delete_ingress_from_a_given_namespace(
        name: str,
        namespace: str
):
    try:
        v1_networking_api = client.NetworkingV1Api()
        v1_networking_api.delete_namespaced_ingress(name=name, namespace=namespace)
        return f"Ingress {name} was deleted from namespace {namespace}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
