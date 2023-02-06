from fastapi import Request, APIRouter, HTTPException
from kubernetes import client, config

router = APIRouter()


@router.get("/api/v1/logs/{namespace}/pod/{name}")
def get_pods_logs_from_given_namespace_api(
        name: str,
        namespace: str
):
    v1_core_api = client.CoreV1Api()
    logs = v1_core_api.read_namespaced_pod_log(name=name, namespace=namespace)
    return {"logs": logs}


@router.get("/api/v1/all-events")
def get_events_for_the_given_namespace():
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
    return {"events": events}


@router.get("/api/v1/events/{namespace}")
def get_events_for_a_given_namespace_api(
        namespace: str
):
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
    return {"events": events_info}


