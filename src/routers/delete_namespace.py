from fastapi import HTTPException, APIRouter
from kubernetes import client

from src.db import delete_namespace_record, delete_all_namespaces_from_db, \
    get_all_namespaces_from_db
from src.namespace import delete_namespace_from_cluster

router = APIRouter()


@router.delete("/namespace/{namespace}")
async def delete_namespace(namespace: str):
    k8s_client = client.CoreV1Api()
    status = []
    try:
        k8s_client.delete_namespace(name=namespace)
        status = delete_namespace_record(namespace)
    except Exception as e:
        status.append(e)
    return status


@router.delete("/namespaces/all")
def delete_all_namespaces():
    try:
        namespaces = get_all_namespaces_from_db()
        if not namespaces:
            raise HTTPException(status_code=404, detail="No namespaces found in the database.")
        for namespace in namespaces:
            delete_namespace_from_cluster(namespace)
        delete_all_namespaces_from_db()
    except Exception as e:
        return e
    return {"message": f"Namespaces {namespaces} have been deleted."}
