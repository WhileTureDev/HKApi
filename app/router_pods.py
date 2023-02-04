from fastapi import APIRouter, HTTPException
from kubernetes import client

router = APIRouter()


@router.get("/api/v1/all-pods")
def get_all_pods_from_cluster_api():
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


@router.get("/api/v1/pods/{namespace}")
def get_pods_from_given_namespace_api(namespace):
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
