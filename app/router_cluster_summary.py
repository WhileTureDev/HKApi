from fastapi import HTTPException, APIRouter
from kubernetes import client, config

router = APIRouter()


@router.get("/api/v1/cluster")
def get_nodes_cluster_summary_api():
    """
        Returns the summary of nodes in the cluster, including the node name, status,
        allocatable memory, allocatable CPU, and allocatable pods.

        Raises:
            HTTPException: If an error occurs during the API call, an HTTPException
                with status code 500 and a detail message will be raised.

        Returns:
            list: List of dictionaries, where each dictionary represents the summary of a node in the cluster.
    """
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
