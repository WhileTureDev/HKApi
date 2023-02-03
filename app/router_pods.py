from fastapi import APIRouter
from kubernetes import client
from starlette.responses import JSONResponse

# from .def_pods import get_pods_namespaced

router = APIRouter()


@router.get("/api/pods{namespace}")
def get_pods_api(namespace):
    pods_list = []
    k8_client = client.CoreV1Api()
    pods = k8_client.list_namespaced_pod(namespace, watch=False)
    for pod in pods.items:
        pod_info = {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "ip": pod.status.pod_ip,
        }
        pods_list.append(pod_info)
    return pods_list

