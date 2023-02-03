from fastapi import HTTPException, APIRouter
from kubernetes import client

from .db import delete_namespace_record, delete_all_namespaces_from_db, \
    get_all_namespaces_from_db
from .def_namespace import delete_namespace_from_cluster

router = APIRouter()


@router.delete("/namespace/{namespace}")
async def delete_namespace_api(namespace: str):
    k8s_client = client.CoreV1Api()
    try:
        k8s_client.delete_namespace(name=namespace)
        delete_namespace_record(namespace)
        return f"Namespace {namespace} was deleted"
    except Exception as e:
        return e


@router.delete("/namespaces/all")
def delete_all_namespaces_api():
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
