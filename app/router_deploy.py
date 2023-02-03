import os
import subprocess
from fastapi import Request, APIRouter, HTTPException
from starlette.responses import JSONResponse

from .db import create_namespace_record, get_deployments_db
from .def_namespace import create_namespace, check_if_namespace_exist

router = APIRouter()


# Read all deployments from database
@router.get("/api/deployments")
def deployments_api():
    deployments = get_deployments_db()
    if not deployments:
        raise HTTPException(status_code=204, detail="No namespaces found.")
    return deployments


@router.post("/deploy")
async def deploy_api(request: Request):
    status = []
    try:
        # Get the data from the request body in JSON format
        data = await request.json()

        # Iterate through the list of charts in the data
        for chart in data['charts']:
            chart_name = chart.get("chart_name")
            chart_repo_url = chart.get("chart_repo_url")
            release_name = chart.get("release_name")
            provider = chart.get("provider")
            namespace = chart.get("namespace")

            # Check if the helm repo exists
            repo_output = subprocess.run(["helm", "repo", "list"], capture_output=True)
            if str(provider) in repo_output.stdout.decode():
                print(f"{provider} already exists")
            else:
                subprocess.run(["helm", "repo", "add", provider, chart_repo_url])
                print(f"{provider} added")

            # Check if the namespace exists, create it if it doesn't
            if not check_if_namespace_exist(namespace):
                create_namespace(namespace)
                # Upgrade or install the chart in the namespace
            subprocess.run(
                ["helm", "upgrade", "--install", release_name, provider + "/" + chart_name, "--namespace",
                 namespace],
                capture_output=True)
            # Update the database with the new chart information

            release_status = subprocess.run(["helm", "status", release_name, "--namespace", namespace],
                                            capture_output=True)
            create_namespace_record(chart_name, chart_repo_url, namespace)
            status.append({
                "chart_name": chart_name,
                "chart_repo_url": chart_repo_url,
                "release_name": release_name,
                "provider": provider,
                "namespace": namespace,
                "repo_output": repo_output.stdout.decode(),
                "release_status": release_status.stdout.decode()
            })
    except subprocess.CalledProcessError as e:
        status.append(e.stderr)
    return JSONResponse(status, status_code=200)
