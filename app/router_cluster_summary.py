from fastapi import HTTPException, APIRouter
from kubernetes import client, config

router = APIRouter()


@router.get("/cluster")
def get_cluster_summary_api():
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
