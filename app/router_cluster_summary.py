import subprocess

from fastapi import HTTPException, APIRouter
from kubernetes import client, config

router = APIRouter()


@router.get("/api/v1/cluster")
def get_nodes_cluster_summary_api():
    try:
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        nodes_info = []
        for node in nodes.items:
            nodes_info.append({
                "name": node.metadata.name,
                "status": node.status.conditions[-1].status,
                "memory": node.status.allocatable["memory"],
                "cpu": node.status.allocatable["cpu"],
                "pods": node.status.allocatable["pods"],
            })
        return nodes_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/ku /cluster/info")
def get_kubernetes_cluster_name():
    try:
        cluster_info = subprocess.run(["kubectl", "config", "view"], capture_output=True)
        return cluster_info.stdout.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/cluster_info")
def get_cluster_info():
    v1_custom_api = client.CustomObjectsApi()
    v1_core_api = client.CoreV1Api()
    v1_aps_api = client.AppsV1Api()
    try:
        cluster_info = {}
        # cluster_info["Cluster Name"] = v1.read_cluster_version().version

        nodes = v1_core_api.list_node().items
        cluster_info["Cluster Size"] = len(nodes)
        node_config = {}
        for node in nodes:
            node_config[node.metadata.name] = {
                "CPU": node.status.capacity["cpu"],
                "Memory": node.status.capacity["memory"],
                "Disk": node.status.capacity["ephemeral-storage"],
            }
        cluster_info["Node Configuration"] = node_config

        cluster_config = v1_custom_api.list_cluster_custom_object("cluster.x-k8s.io", "v1", "clusters")
        cluster_info["Cluster Configuration"] = cluster_config.items[0].spec

        namespaces = v1_core_api.list_namespace().items
        namespace_list = {}
        for ns in namespaces:
            pods = v1_core_api.list_namespaced_pod(ns.metadata.name).items
            pod_list = []
            for pod in pods:
                pod_list.append({
                    "Name": pod.metadata.name,
                    "Status": pod.status.phase,
                    "IP": pod.status.pod_ip,
                })
            services = v1_core_api.list_namespaced_service(ns.metadata.name).items
            service_list = []
            for service in services:
                service_list.append({
                    "Name": service.metadata.name,
                    "Type": service.spec.type,
                    "IP": service.spec.cluster_ip,
                })
            namespace_list[ns.metadata.name] = {
                "Pods": pod_list,
                "Services": service_list,
            }
        cluster_info["Namespaces"] = namespace_list

        deployments = v1_aps_api.list_namespaced_deployment("default").items
        deployment_list = []
        for deployment in deployments:
            deployment_list.append({
                "Name": deployment.metadata.name,
                "Replicas": deployment.spec.replicas,
                "Image": deployment.spec.template.spec.containers[0].image,
            })
        cluster_info["Deployments"] = deployment_list

        storage = v1_core_api.list_persistent_volume().items
        storage_list = []
        for pv in storage:
            storage_list.append({
                "Name": pv.metadata.name,
                "Storage Class": pv.spec.storage_class_name,
                "Status": pv.status.phase,
                "Capacity": pv.spec.capacity["storage"],
            })
        cluster_info["Storage"] = storage_list
        return cluster_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
