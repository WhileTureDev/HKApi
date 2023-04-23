from fastapi import APIRouter, Body, HTTPException, Depends
from kubernetes import client
from fastapi.responses import JSONResponse


from .db import delete_namespace_record
from pydantic import BaseModel
from .crud_user import get_current_active_user
router = APIRouter()


class NamespacePayload(BaseModel):
    labels: dict


"""
NamespacePayload: Model for the namespace creation request payload

Attributes:
labels (dict): Key-value pairs of labels to be applied to the namespace
"""


@router.post("/api/v1/create/namespaces", dependencies=[Depends(get_current_active_user)])
async def create_namespace(namespace_spec: dict = Body(..., embed=False)):
    """Create a namespace in the cluster.

    Route to create a namespace in the cluster, given a namespace specification.

    Parameters:
    namespace_spec (dict, optional): The specification for the namespace to be created.
    The default is a required JSON body with embed=False.

    Raises:
    HTTPException: If an error occurs while creating the namespace.

    Returns:
    str: A message indicating that the namespace was created.
    """
    try:
        v1_core_api = client.CoreV1Api()
        namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_spec['metadata']['name']))
        v1_core_api.create_namespace(body=namespace)
        return "Namespace was created "
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/list-all-namespaces", dependencies=[Depends(get_current_active_user)])
def get_all_namespaces():
    """
    Get a list of all namespaces in the cluster.

    Returns:
    JSON object containing a list of all namespaces with their names and statuses.

    Raises:
    HTTPException: If there is an error retrieving the namespaces from the cluster.
    """

    try:
        v1_core_api = client.CoreV1Api()
        namespaces = v1_core_api.list_namespace().items
        results = []
        for namespace in namespaces:
            results.append({
                "name": namespace.metadata.name,
                "status": namespace.status.phase
            })
        return JSONResponse(status_code=200, content=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/api/v1/update-namespace/{namespace_name}", dependencies=[Depends(get_current_active_user)])
async def update_namespace(namespace_name: str, payload: NamespacePayload):
    """
    This function updates the labels of an existing namespace in the Kubernetes cluster.

    :param namespace_name: Name of the namespace to be updated.
    :type namespace_name: str
    :param payload: A NamespacePayload object containing the labels to be updated.
    :type payload: NamespacePayload
    :return: A dictionary containing the message of success and the updated namespace's information.
    :rtype: Dict[str, Union[str, Dict]]
    :raises HTTPException: If there is an error updating the namespace, a 500 HTTP error is raised with details.
    """

    try:
        v1_core_api = client.CoreV1Api()
        namespace = v1_core_api.read_namespace(name=namespace_name)
        namespace.metadata.labels.update(payload.labels)
        namespace = v1_core_api.patch_namespace(name=namespace_name, body=namespace)
        return {"message": "Namespace updated successfully", "namespace": namespace.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/v1/namespace/{namespace}", dependencies=[Depends(get_current_active_user)])
async def delete_namespace_api(namespace: str):
    """
    This function deletes a namespace from the Kubernetes cluster.

    :param namespace: The name of the namespace to delete.
    :type namespace: str
    :return: A message indicating the namespace was deleted.
    :rtype: str
    :raises HTTPException: If an error occurs while deleting the namespace, an HTTPException is raised with a status code of 500 and a detail message indicating the error.
    """

    k8s_client = client.CoreV1Api()
    try:
        k8s_client.delete_namespace(name=namespace)
        delete_namespace_record(namespace)
        return f"Namespace {namespace} was deleted"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
