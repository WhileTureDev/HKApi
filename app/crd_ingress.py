from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Body
from kubernetes import client
from pydantic import BaseModel

router = APIRouter()


@router.get("/api/v1/namespaces/{namespace_name}/ingresses")
async def list_ingresses_by_namespace(namespace_name: str):
    """
    Lists all ingresses in a specified namespace.

    Route:
    @app.get("/api/v1/namespaces/{namespace_name}/ingresses")

    Input:
    namespace_name: str
    The name of the namespace.

    Returns:
    list
    A list of dictionaries, each dictionary contains the name, namespace, rules for the respective ingress.
    Rules are represented as a list of dictionaries, each of which has a host and paths attributes.

    Raises:
    HTTPException:
    If an error occurs while getting ingresses in the specified namespace,
    this function will raise an exception with a status code of 500 and detail message of the error.
    """
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
    """Create an ingress in a specified namespace.

    Arguments:
        ingress_spec (dict): A dictionary containing the ingress specification, including metadata and spec.

    Returns: dict: A dictionary with a message indicating whether the ingress was created or not and, in case of
    error, additional details.
    """
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


"""
Class UpdateIngressResponse:
Model for storing the information of a updated ingress.
"""


@router.delete("/api/v1/delete/namespaces/{namespace_name}/ingresses/{ingress_name}")
def delete_ingress_from_a_given_namespace(
        name: str,
        namespace: str
):
    """
    Delete an ingress from a given namespace in the cluster.

    :param name: The name of the ingress to be deleted.
    :param namespace: The namespace from which the ingress will be deleted.
    :return: A string message indicating if the ingress was successfully deleted.
    :raises: HTTPException if an error occurs during the deletion.
    """
    try:
        v1_networking_api = client.NetworkingV1Api()
        v1_networking_api.delete_namespaced_ingress(name=name, namespace=namespace)
        return f"Ingress {name} was deleted from namespace {namespace}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
