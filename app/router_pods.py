from fastapi import APIRouter, Depends
from kubernetes import client
from .crud_user import get_current_active_user
router = APIRouter()


@router.get("/api/v1/all-pods", dependencies=[Depends(get_current_active_user)])
def get_all_pods_from_cluster_api():
    """
    Get information about all the pods in a cluster.

    Returns:
    A list of dictionaries, each containing information about a single pod in the cluster:
    - name: the name of the pod.
    - namespace: the namespace to which the pod belongs.
    - status: the current status of the pod (e.g. "Running").
    - ip: the IP address of the pod.
    """

    k8_client = client.CoreV1Api()
    pods = k8_client.list_pod_for_all_namespaces()
    results = []
    for pod in pods.items:
        pod_info = {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ip": pod.status.pod_ip,
        }
        results.append(pod_info)
    return results


@router.get("/api/v1/pods/{namespace}", dependencies=[Depends(get_current_active_user)])
def get_pods_from_given_namespace_api(namespace):
    """
    Get the pods from a given namespace in the Kubernetes cluster.

    Args:
    namespace (str): The namespace from which to retrieve the pods.

    Returns: list: A list of dictionaries containing information about each pod, including its name, namespace,
    status, and IP address.

    Raises:
    HTTPException: If there is an error in retrieving the pods from the given namespace.
    """

    k8_client = client.CoreV1Api()
    pods = k8_client.list_namespaced_pod(namespace, watch=False)
    results = []
    for pod in pods.items:
        pod_info = {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ip": pod.status.pod_ip,
        }
        results.append(pod_info)
    return results
