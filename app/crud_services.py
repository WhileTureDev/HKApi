from fastapi import APIRouter, HTTPException
from kubernetes import client

router = APIRouter()


@router.get("/api/v1/get/services/{namespace}")
def get_all_services_in_a_namespace(namespace):
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


@router.get("/api/v1/get/all-services/")
def get_all_services_from_cluster():
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


@router.delete("/api/v1/delete/{namespace}/service/name")
async def delete_service_api(
        name: str,
        namespace: str
):
    try:
        v1_core_api = client.CoreV1Api()
        v1_core_api.delete_namespaced_service(name=name, namespace=namespace)
        return {"message": f"Service {name} successfully deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
