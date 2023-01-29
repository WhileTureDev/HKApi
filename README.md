# Deploy Helm Charts API

This API allows for the deployment of Helm charts to a Kubernetes cluster. Each environment is isolated by namespaces, and the Helm charts are taken from a given Helm chart repository. The API supports Helm 3.

## Architecture

The API consists of the following components:

- A Python script that handles the deployment of Helm charts using the Kubernetes Python client and the subprocess library.
- A SQLite database that stores the namespaces and deploy names for each deployment.
- FastAPI for creating the API endpoints.
- Uvicorn for running the server.

The API has the following endpoints:

- `/deploy`: Deploys a Helm chart to a namespace. The endpoint takes the following parameters:
    - `chart_name`: The name of the chart to deploy.
    - `chart_repo`: The chart repository from which to retrieve the chart.
    - `namespace`: The namespace to deploy the chart to. If not specified, a random namespace will be generated.
    - `values`: Values to pass to the chart during deployment.

- `/list`: List all the deployments

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Docker
- Kubernetes cluster

### Installing

- Clone the repository:
```shell
git clone https://github.com/steerCI/HKApi.git
```

- Build the Docker image:
```shell
docker build -t helm-charts-api 
```

- Run the container:

```shell
docker run -p 8000:8000 helm-charts-api
```

- Test the API by sending a POST request to `http://localhost:8000/deploy` with the required parameters.

## Deployment

To deploy the API to a Kubernetes cluster, you can use the provided Kubernetes manifests in the `k8s` directory.

1. Create the ConfigMap:
```shell
kubectl apply -f k8s/configmap.yaml
```

2. Create the Deployment:

```shell
kubectl apply -f k8s/deployment.yaml
```
- Create the Service:
```shell
kubectl apply -f k8s/service.yaml
```


4. Access the API via the Service's external IP or NodePort.

## Built With

- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used
- [SQLite](https://www.sqlite.org/index.html) - Database
- [Uvicorn](https://www.uvicorn.org/) - ASGI server
- [kubernetes-python-client](https://pypi.org/project/kubernetes-python-client/) - Python client for the Kubernetes API


## Usage

To deploy a chart to a namespace, send a POST request to the /deploy/{namespace} endpoint with a JSON payload containing the chart name and chart repository URL.

Example payload:
```json
{
    "charts": [
        {
            "chart_name": "jenkins",
            "chart_repo_url": "https://charts.bitnami.com/bitnami",
            "release_name": "jenkins-app",
            "provider": "bitnami"
        },
        {
            "chart_name": "wordpress",
            "chart_repo_url": "https://charts.bitnami.com/bitnami",
            "release_name": "wordpress-app",
            "provider": "bitnami"
        }
    ]
}
```
## Authors

* **Your Name** - *Initial work* - [cradules](https://github.com/cradules)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details



