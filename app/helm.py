import subprocess

from fastapi import Request, APIRouter, HTTPException, Depends
from starlette.responses import JSONResponse
import json
from .def_namespace import create_namespace, check_if_namespace_exist
from .crud_user import get_current_active_user
from .schemas import BaseHelmReleaseInfo, CreateHelmReleaseInfo, DeleteHelmReleaseInfo
import subprocess
import logging

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)


# Create helm release endpoint
@router.post("/api/v1/helm/create", dependencies=[Depends(get_current_active_user)])
async def create_helm_release_api(release_info: CreateHelmReleaseInfo):
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
        # # Get the data from the request body in JSON format
        # data = await request.json()

        # Iterate through the list of charts in the data

        release_name = release_info.name
        chart_name = release_info.chart_name
        chart_repo_url = release_info.chart_repo_url
        provider = release_info.provider
        namespace = release_info.namespace

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

            # Attempt Helm upgrade/install
            helm_command = ["helm", "upgrade", "--install", release_name, provider + "/" + chart_name,
                            "--namespace", namespace]
            logging.info(f"Executing Helm command: {helm_command}")
            result = subprocess.run(helm_command, capture_output=True)

            if result.returncode != 0:
                error_msg = f"Helm command failed with exit code {result.returncode}: {result.stderr.decode()}"
                logging.error(error_msg)
                status.append(error_msg)
            else:

                # Update the database with the new chart information

                release_status = subprocess.run(["helm", "status", release_name, "--namespace", namespace],
                                                capture_output=True)
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
    return JSONResponse(status_code=200, content=status)


# Delete helm release endpoint
@router.delete("/api/v1/helm/delete", dependencies=[Depends(get_current_active_user)])
async def delete_helm_release(release_info: DeleteHelmReleaseInfo):  # Use a data model
    """
    Delete the Helm release.

    Args:
        release_info (ReleaseInfo): Data model containing release name and namespace.

    Returns:
        dict: JSON response with a message indicating success or failure.
    """
    try:
        result = subprocess.run(
            ["helm", "delete", release_info.name, "--namespace", release_info.namespace],
            capture_output=True,
            text=True  # Capture output as text for easier decoding
        )

        if result.returncode != 0:  # Check the return code for success/failure
            if "not found" in result.stderr.lower():
                return {
                    "message": f"Helm release {release_info.name} does not exist in namespace {release_info.namespace}"}
            else:
                raise HTTPException(status_code=500, detail=result.stderr)  # Return the actual error from Helm
        else:
            return {"message": f"Helm release {release_info.name} deleted"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))


# Status helm release
@router.get("/api/v1/helm/status", dependencies=[Depends(get_current_active_user)])
async def status_helm_release(release_info: BaseHelmReleaseInfo):
    try:
        result = subprocess.run(
            ["helm", "status", release_info.name, "--namespace", release_info.namespace],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Parse Helm output into a dictionary
            status_lines = result.stdout.strip().split("\n")
            status_dict = {}
            for line in status_lines:
                if ":" in line:  # Add check if ":" exists in line.
                    key, value = line.split(":", 1)
                    status_dict[key.strip()] = value.strip()
                else:
                    logging.warning(f"Unexpected line in Helm status output: {line}")  # Log the unexpected line
            return {"Name": release_info.name, "Namespace": release_info.namespace, "Info": status_dict}
        else:
            error_message = result.stderr.strip()
            if "not found" in error_message.lower():
                return {
                    "message": f"Helm release {release_info.name} does not exist in namespace {release_info.namespace}"}
            else:
                raise HTTPException(status_code=500, detail=f"Error getting Helm status: {error_message}")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))
