from fastapi import Request, APIRouter, HTTPException
from kubernetes import client, config

router = APIRouter()


@router.get("/api/v1/list-all/nodes")
async def list_all_nodes_in_cluster():
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
