import random
import string
from kubernetes import client


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
