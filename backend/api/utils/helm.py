import subprocess
import json
import tempfile
import yaml
from kubernetes import client, config
from typing import List, Optional, Union, Dict
from urllib.parse import urlparse
import os

# In-memory storage for helm repositories
helm_repositories = {}

def load_k8s_config():
    try:
        config.load_incluster_config()
        print("Using in-cluster K8s configuration")
    except config.config_exception.ConfigException:
        config.load_kube_config()
        print("Using local K8s configuration")


def add_helm_repo(repo_name: str, repo_url: str) -> bool:
    try:
        subprocess.run([
            "helm", "repo", "add", repo_name, repo_url
        ], check=True)
        subprocess.run([
            "helm", "repo", "update"
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error adding Helm repository: {e}")
        return False


def deploy_helm_chart_combined(
    release_name: str,
    chart_name: str,
    chart_repo_url: str,
    namespace: str,
    values: Optional[Dict[str, Union[str, int, float, bool, None]]] = None,
    values_file_path: Optional[str] = None,
    version: Optional[str] = None,
    debug: bool = False
) -> int:
    try:
        load_k8s_config()
        v1 = client.CoreV1Api()

        # Check if the namespace exists
        namespaces = v1.list_namespace()
        if namespace not in [ns.metadata.name for ns in namespaces.items]:
            # Create the namespace if it does not exist
            namespace_body = client.V1Namespace(
                metadata=client.V1ObjectMeta(name=namespace)
            )
            v1.create_namespace(namespace_body)

        # Add Helm repository
        repo_name = os.path.basename(chart_repo_url.strip('/'))
        if not add_helm_repo(repo_name, chart_repo_url):
            raise Exception("Failed to add Helm repository")

        # Create a temporary values.yaml file if values are provided
        temp_file_name = None
        if values is not None:
            with tempfile.NamedTemporaryFile('w', delete=False) as temp_file:
                yaml.dump(values, temp_file)
                temp_file_name = temp_file.name

        # Prepare Helm command
        helm_command = [
            "helm", "upgrade", "--install", release_name, f"{repo_name}/{chart_name}",
            "--namespace", namespace
        ]

        if temp_file_name:
            helm_command.extend(["-f", temp_file_name])
        elif values_file_path:
            helm_command.extend(["-f", values_file_path])

        # If a specific version is provided, add the --version flag
        if version:
            helm_command.extend(["--version", version])

        # Add --debug flag if debug mode is enabled
        if debug:
            helm_command.append("--debug")

        # Deploy or upgrade the Helm chart
        subprocess.run(helm_command, check=True)

        # Fetch the Helm revision
        result = subprocess.run([
            "helm", "history", release_name, "--namespace", namespace, "--max", "1"
        ], check=True, capture_output=True, text=True)

        revision = int(result.stdout.splitlines()[-1].split()[0])

        # Clean up the temporary file
        if temp_file_name:
            os.remove(temp_file_name)

        return revision
    except (subprocess.CalledProcessError, client.exceptions.ApiException) as e:
        print(f"Error during Helm chart deployment: {e}")
        return -1


def delete_helm_release(release_name: str, namespace: str) -> bool:
    try:
        load_k8s_config()
        subprocess.run([
            "helm", "uninstall", release_name, "--namespace", namespace
        ], check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        if "release: not found" in e.stderr:
            print(f"Release {release_name} not found in namespace {namespace}")
            return False
        print(f"Error during Helm chart deletion: {e}")
        return False


def list_helm_releases(namespace: Optional[str] = None) -> List[dict]:
    try:
        command = ["helm", "list", "--all", "--output", "json"]
        if namespace:
            command.extend(["--namespace", namespace])
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error listing Helm releases: {e}")
        return []


def get_helm_values(release_name: str, namespace: Optional[str] = None) -> dict:
    try:
        command = ["helm", "get", "values", release_name, "--output", "json"]
        if namespace:
            command.extend(["--namespace", namespace])
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting values for release {release_name}: {e}")
        return {}


def rollback_helm_release(release_name: str, revision: int, namespace: str, force: bool = False,
                          recreate_pods: bool = False) -> bool:
    try:
        command = ["helm", "rollback", release_name, str(revision), "--namespace", namespace]

        if force:
            command.append("--force")

        if recreate_pods:
            command.append("--recreate-pods")

        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during rollback: {e}")
        return False


def get_helm_status(release_name: str, namespace: Optional[str] = None) -> dict:
    try:
        command = ["helm", "status", release_name, "--output", "json"]
        if namespace:
            command.extend(["--namespace", namespace])
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting status for release {release_name}: {e}")
        return {}


def configure_helm_repositories():
    """Configure Helm repositories from in-memory storage"""
    for repo_name, repo_url in helm_repositories.items():
        try:
            add_helm_repo(repo_name, repo_url)
        except Exception as e:
            print(f"Error configuring repository {repo_name}: {str(e)}")


def extract_repo_name_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    # Use the full domain name as the repository name (e.g., 'cloudecho.github.io' from
    # 'https://cloudecho.github.io/charts/')
    repo_name = parsed_url.netloc
    return repo_name


def search_helm_charts(term: str, repositories: List[str]) -> List[dict]:
    search_results = []
    for repo in repositories:
        try:
            command = ["helm", "search", "repo", repo, "--output", "json"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            charts = json.loads(result.stdout)
            filtered_charts = [chart for chart in charts if term.lower() in chart["name"].lower()]
            search_results.extend(filtered_charts)
        except subprocess.CalledProcessError as e:
            print(f"Error searching Helm repository {repo}: {e}")
    return search_results


def update_helm_repositories() -> bool:
    try:
        command = ["helm", "repo", "update"]
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error updating Helm repositories: {e}")
        return False


def get_helm_release_history(release_name: str, namespace: Optional[str] = None) -> List[dict]:
    try:
        command = ["helm", "history", release_name, "--output", "json"]
        if namespace:
            command.extend(["--namespace", namespace])
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting history for release {release_name}: {e}")
        return []


def list_all_helm_releases() -> List[dict]:
    try:
        command = ["helm", "list", "--all-namespaces", "--output", "json"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error listing all Helm releases: {e}")
        return []


def list_helm_charts_in_repo(repo_name: str) -> List[dict]:
    try:
        command = ["helm", "search", "repo", repo_name, "--output", "json"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error listing charts in repository {repo_name}: {e}")
        return []


def get_helm_release_notes(release_name: str, revision: int, namespace: str) -> str:
    try:
        command = ["helm", "history", release_name, "--namespace", namespace, "--output", "json"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        history = json.loads(result.stdout)

        for entry in history:
            if entry['revision'] == revision:
                return entry.get('description', 'No notes available')

        return 'Revision not found'
    except subprocess.CalledProcessError as e:
        print(f"Error getting history for release {release_name}: {e}")
        return 'Error retrieving release notes'


def export_helm_release_values_to_file(release_name: str, namespace: str) -> str:
    try:
        command = ["helm", "get", "values", release_name, "--namespace", namespace, "--output", "yaml", "--all"]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as temp_file:
            temp_file.write(result.stdout.encode('utf-8'))
            temp_file_name = temp_file.name
            print(f"Temporary file created at: {temp_file_name}")
            print(f"File content: {result.stdout}")
            return temp_file_name
    except subprocess.CalledProcessError as e:
        print(f"Error exporting values for release {release_name}: {e}")
        return None
