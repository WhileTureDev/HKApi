import random
import string
from kubernetes import client


def check_if_namespace_exist(ns_name: str):
    v1 = client.CoreV1Api()
    try:
        v1.read_namespace(name=ns_name)
        return True
    except Exception as e:
        return e


def create_namespace():
    v1 = client.CoreV1Api()
    body = client.V1Namespace()
    ns_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    body.metadata = client.V1ObjectMeta(name=ns_name)
    try:
        v1.create_namespace(body)
        return ns_name
    except Exception as e:
        return e
