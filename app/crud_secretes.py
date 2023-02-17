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
    """
    Create a Kubernetes secret in a specific namespace

    Route: POST /api/v1/secrets/{namespace}/secrets/{name}

    Params:

    namespace: str: The namespace in which the secret should be created.
    name: str: The name of the secret to be created.
    data: Dict[str, str]: The data to be stored in the secret.
    Returns:

    A list containing a dictionary of the created secret's information including:
    name: The name of the secret.
    namespace: The namespace of the secret.
    data: The data stored in the secret.
    Raises:

    HTTPException: If an error occurs during the creation of the secret.
    The status_code will be 500 and the detail will contain the error message.

    """

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
    """
    This endpoint returns a list of secrets for the given namespace.

   Args:
       namespace (str): The name of the namespace to retrieve secrets from.
   Returns:
       dict: A dictionary containing the secrets from the given namespace. The dictionary has the following structure:
       {
           "secrets": [
               {
                   "name": str,
                   "namespace": str,
                   "data": dict
               },
               ...
           ]
       }
   Raises:
       HTTPException: In case of any error while retrieving secrets from the namespace, it raises an HTTPException with
       status code 500 and a detail message explaining the error.
    """

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
    """
    Get the information of a specific secret from a given namespace.

    :param namespace: The name of the namespace to retrieve secrets from.
    :param name: The name of the secret to retrieve. :type name: str :param namespace: The name of the namespace
    where the secret is located. type namespace: str :return: A dictionary containing the information of the secret.
    The dictionary includes the name, namespace, and data of the secret. :rtype: Dict[str, Union[str, Dict[str,
    str]]] :raises HTTPException: If there is an error while retrieving the secret information. The status code of
    the exception is set to 500 and the detail message of the exception is the error message.

    """

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
    """
    Edit a secret in a given namespace in the Kubernetes cluster.

    :param name: The name of the secret.
    :param namespace: The namespace of the secret.
    :param data: The data to update the secret with.
    :return: The updated secret information, including name, namespace and data.
    :raises: HTTPException with status code 500 if an error occurs.

    """

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
    """

    Delete a Secret from the given Namespace.

    Args:
        name (str): The name of the Secret to be deleted.
        namespace (str): The namespace where the Secret is located.

    Returns:
        dict: A dictionary containing a message confirming the successful deletion of the Secret.

    Raises:
        HTTPException: If an error occurs while deleting the Secret, an HTTPException with a status code of 500 and
        a detail message describing the error is raised.

    """

    try:
        v1_core_api = client.CoreV1Api()
        v1_core_api.delete_namespaced_secret(name=name, namespace=namespace)
        return {"message": f"Secret {name} successfully deleted form namespace  {namespace}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
