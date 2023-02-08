import subprocess

from fastapi import Request, APIRouter, HTTPException
from starlette.responses import JSONResponse

from .db import create_namespace_record
from .def_namespace import create_namespace, check_if_namespace_exist

router = APIRouter()


@router.post("/api/v1/create-helm-release")
async def create_helm_release_api(request: Request):
    """
    Create Helm Release API

    This API is used to install/upgrade Helm charts from a chart repository and create/update the record in the database.

    Request Body:
    A list of dictionaries, where each dictionary contains information about a chart and its release.
    The required keys for each dictionary are:
    - chart_name: The name of the chart to be installed/upgraded
    - chart_repo_url: The URL of the chart repository
    - release_name: The name of the release
    - provider: The name of the chart repository provider
    - namespace: The name of the namespace to install/upgrade the chart to

    Response Body:
    A list of dictionaries, where each dictionary contains information about a chart installation/upgrade status.
    The keys in each dictionary are:
    - chart_name: The name of the chart installed/upgraded
    - chart_repo_url: The URL of the chart repository
    - release_name: The name of the release
    - provider: The name of the chart repository provider
    - namespace: The name of the namespace the chart was installed/upgraded to
    - repo_output: The output of the 'helm repo list' command
    - release_status: The output of the 'helm status' command

    Raises:
    HTTPException: If there is an error in the installation/upgrade process.
    """

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


@router.delete("/api/v1/delete/{namespace}/helm/{name}")
async def delete_helm_release_from_given_namespace(
        name: str,
        namespace: str
):
    """
    Delete the Helm release from a given namespace.

    Args:
    name (str): The name of the Helm release to delete.
    namespace (str): The namespace the Helm release is in.

    Returns:
    dict: JSON response with a message indicating success or failure.

    Raises:
    HTTPException: When the operation fails, an HTTPException with a status code of 500 and the error message is raised.
    """

    try:
        subprocess.run(["helm", "delete", f"{name}", "--namespace", f"{namespace}"], capture_output=True)
        return {"message": f"Helm release {name} deleted"}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
