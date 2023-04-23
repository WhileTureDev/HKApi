from fastapi import APIRouter, Depends
from kubernetes import client
from fastapi.responses import JSONResponse

from .crud_user import get_current_active_user

router = APIRouter()


@router.get("/api/v1/logs/{namespace}/pod/{name}", dependencies=[Depends(get_current_active_user)])
def get_pods_logs_from_given_namespace_api(
        name: str,
        namespace: str
):
    """
    Get logs of a pod in a given namespace.

    Args:
    name (str): name of the pod.
    namespace (str): namespace the pod is in.

    Returns:
    Dict: A dictionary containing the logs of the pod, with the key 'logs'.

    Raises:
    Exception: If any error occurs during the process, it will raise the exception with a detail of the error.
    """
    v1_core_api = client.CoreV1Api()
    logs = v1_core_api.read_namespaced_pod_log(name=name, namespace=namespace)
    return JSONResponse(status_code=200, content=logs)


@router.get("/api/v1/all-events")
def get_events_for_the_all_namespaces_in_cluster():
    """
    Get events for all namespaces.

    Returns:
        A dictionary containing a key `events` with a list of dictionaries, each representing
        an event with the following keys:
    """
    events = []
    v1_core_api = client.CoreV1Api()
    for event in v1_core_api.list_event_for_all_namespaces().items:
        events.append({
            "event_name": event.metadata.name,
            "namespace": event.metadata.namespace,
            "event_type": event.type,
            "object": event.involved_object.kind,
            "message": event.message,
            "reason": event.reason,
            "time": event.last_timestamp
        })
    return JSONResponse(status_code=200, content=events)


@router.get("/api/v1/events/{namespace}", dependencies=[Depends(get_current_active_user)])
def get_events_for_a_given_namespace_api(
        namespace: str
):
    """
    Retrieve events for a given namespace from the Kubernetes cluster.

    :param namespace: The namespace for which to retrieve events.
    :type namespace: str

    :return: A dictionary containing a list of events for the given namespace. Each event is represented as a dictionary with the following keys:

    "name": the name of the event
    "namespace": the namespace in which the event occurred
    "event_type": the type of the event
    "object": the kind of object involved in the event
    "message": the message of the event
    "reason": the reason for the event
    "time": the last timestamp of the event
    :rtype: dict
    """

    v1_core_api = client.CoreV1Api()
    events = v1_core_api.list_namespaced_event(namespace=namespace)
    events_info = []
    for event in events.items:
        events_info.append({
            "name": event.metadata.name,
            "namespace": event.metadata.namespace,
            "event_type": event.type,
            "object": event.involved_object.kind,
            "message": event.message,
            "reason": event.reason,
            "time": event.last_timestamp
        })
    return JSONResponse(status_code=200, content=events_info)
