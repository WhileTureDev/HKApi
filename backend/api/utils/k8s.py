from kubernetes import client, config


def get_deployment_status(namespace: str, name: str):
    config.load_kube_config()
    v1 = client.AppsV1Api()
    try:
        deployment = v1.read_namespaced_deployment(name, namespace)
        return {
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "status": deployment.status.conditions[-1].type,
            "message": deployment.status.conditions[-1].message,
            "replicas": deployment.status.replicas,
            "available_replicas": deployment.status.available_replicas,
            "unavailable_replicas": deployment.status.unavailable_replicas,
        }
    except client.exceptions.ApiException as e:
        print(f"Exception when calling AppsV1Api->read_namespaced_deployment: {e}")
        return None
