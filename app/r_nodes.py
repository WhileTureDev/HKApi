from fastapi import Request, APIRouter, HTTPException
from kubernetes import client, config

router = APIRouter()


@router.get("/api/v1/list-all/nodes")
async def list_all_nodes_in_cluster():
    """
    get_all_nodes_in_cluster

    Returns the list of all nodes in the Kubernetes cluster, including their name, IP, CPU usage, memory usage, number of pods, and node conditions.

    Returns:
    A list of dictionaries containing information about each node. Each dictionary has the following keys:
    - name: The name of the node.
    - IP: The IP address of the node.
    - cpu_usage: The CPU usage of the node.
    - memory_usage: The memory usage of the node.
    - pods: The number of pods in the node.
    - node_conditions: A list of dictionaries, each containing information about a node condition. Each dictionary has the following keys:
    - type: The type of the condition.
    - status: The status of the condition.
    """
    v1_core_api = client.CoreV1Api()
    nodes = v1_core_api.list_node()
    results = []
    for node in nodes.items:
        nodes_info = {
            "name": node.metadata.name,
            "IP": node.status.addresses[0].address,
            "cpu_usage": node.status.capacity["cpu"],
            "memory_usage": node.status.capacity["memory"],
            "pods": node.status.capacity["pods"],
            "node_conditions": [
                {
                    "type": condition.type,
                    "status": condition.status
                } for condition in node.status.conditions
            ]
        }
        results.append(nodes_info)
    return results
