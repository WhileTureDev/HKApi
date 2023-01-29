from kubernetes import client
from kubernetes.client import ApiException
from fastapi import HTTPException


def check_if_namespace_exist(namespace: str):
    v1 = client.CoreV1Api()
    try:
        v1.read_namespace(name=namespace)
        return True
    except Exception:
        return False


def create_namespace(namespace):
    v1 = client.CoreV1Api()
    body = client.V1Namespace()
    # ns_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    body.metadata = client.V1ObjectMeta(name=namespace)
    try:
        v1.create_namespace(body)
        return namespace
    except Exception as e:
        return e


def delete_namespace_from_cluster(namespace_name: str):
    v1 = client.CoreV1Api()
    try:
        v1.delete_namespace(namespace_name)
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.reason)
