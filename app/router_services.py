from fastapi import APIRouter
from kubernetes import client

router = APIRouter()


@router.get("/api/services/{namespace}")
def get_services(namespace):
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
    return results


@router.get("/api/services-all/")
def get_all_services():
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
    return results
