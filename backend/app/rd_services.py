from fastapi import APIRouter, HTTPException, Depends
from kubernetes import client
from fastapi.responses import JSONResponse

from .crud_user import get_current_active_user


router = APIRouter()


@router.get("/api/v1/get/services/{namespace}", dependencies=[Depends(get_current_active_user)])
def get_all_services_in_a_namespace(namespace):
    """
    This function returns the list of all services in the specified namespace.

    :param namespace: The name of the namespace.
    :type namespace: str
    :return: A list of dictionaries, each dictionary representing a service in the namespace.
    The dictionary contains the following keys:
    - name (str): The name of the service.
    - namespace (str): The namespace of the service.
    - type (str): The type of the service.
    - internal_ip (str): The internal IP address of the service.
    - external_ip (list): A list of external IP addresses of the service.
    :rtype: list of dictionaries
    """

    k8_client = client.CoreV1Api()
    services = k8_client.list_namespaced_service(namespace, watch=False)
    results = []
    for service in services.items:
        result = {
            "name": service.metadata.name,
            "namespace": service.metadata.namespace,
            "type": service.spec.type,
            "internal_ip": service.spec.cluster_ip,
            "external_ip": service.spec.external_i_ps
        }
        results.append(result)
    return JSONResponse(status_code=200, content=results)


@router.get("/api/v1/get/all-services/", dependencies=[Depends(get_current_active_user)])
def get_all_services_from_cluster():
    """
    Get all services in the cluster.

    Returns:
        List of dictionaries containing information about the services in the cluster:
        - name (str): name of the service
        - namespace (str): namespace of the service
        - type (str): type of the service (ClusterIP, NodePort, LoadBalancer, etc)
        - internal_ip (str): internal IP of the service
        - external_ip (List[str]): list of external IPs of the service
    """

    k8_client = client.CoreV1Api()
    services = k8_client.list_service_for_all_namespaces()
    results = []
    for service in services.items:
        result = {
            "name": service.metadata.name,
            "namespace": service.metadata.namespace,
            "type": service.spec.type,
            "internal_ip": service.spec.cluster_ip,
            "external_ip": service.spec.external_i_ps
        }
        results.append(result)
    return JSONResponse(status_code=200, content=results)


@router.delete("/api/v1/delete/{namespace}/service/name", dependencies=[Depends(get_current_active_user)])
async def delete_service_api(
        name: str,
        namespace: str
):
    """
    Delete a Service in a given Namespace

    This endpoint allows to delete a specified Service in a Namespace.

    :type namespace: str  :param namespace: The name of the Namespace.
    :type name: str :param namespace: The name of the Service.
    namespace: str :return: A JSON object containing the message indicating the result of the operation. :rtype: dict
    :raises HTTPException: If an error occurs during the deletion of the Service, an exception is raised with a
    status code of 500. The detail field contains the error message.
    """

    try:
        v1_core_api = client.CoreV1Api()
        v1_core_api.delete_namespaced_service(name=name, namespace=namespace)
        return {"message": f"Service {name} successfully deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
