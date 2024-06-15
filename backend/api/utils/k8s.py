from kubernetes import client, config
import subprocess
import tempfile
import yaml
import os


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


def deploy_helm_chart(release_name: str, chart_name: str, chart_repo_url: str, namespace: str, values: dict) -> int:
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

        # Create a temporary values.yaml file
        with tempfile.NamedTemporaryFile('w', delete=False) as temp_file:
            yaml.dump(values, temp_file)
            temp_file_name = temp_file.name

        # Deploy or upgrade the Helm chart
        subprocess.run([
            "helm", "upgrade", "--install", release_name, f"{repo_name}/{chart_name}",
            "--namespace", namespace,
            "-f", temp_file_name
        ], check=True)

        # Fetch the Helm revision
        result = subprocess.run([
            "helm", "history", release_name, "--namespace", namespace, "--max", "1"
        ], check=True, capture_output=True, text=True)

        revision = int(result.stdout.splitlines()[-1].split()[0])
        return revision
    except (subprocess.CalledProcessError, client.exceptions.ApiException) as e:
        print(f"Error during Helm chart deployment: {e}")
        return -1


def delete_helm_release(release_name: str, namespace: str) -> bool:
    try:
        load_k8s_config()
        subprocess.run([
            "helm", "uninstall", release_name, "--namespace", namespace
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during Helm chart deletion: {e}")
        return False
