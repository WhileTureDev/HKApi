from fastapi import APIRouter
from kubernetes import client
router = APIRouter()


@router.get("/api/pods{namespace}")
def get_pods_api(namespace):
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

