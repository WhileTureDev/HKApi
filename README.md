# HKAPI - Helm&Kubernetes API

## Introduction

The purpose of this project is to empower developers to take control of their own infrastructure by providing them with a powerful API that allows them to deploy and manage services in their own cluster. With this API, 
developers have the ability to deploy services either through Helm charts, Kubernetes manifests, or by direct JSON payloads. 
The API also provides a comprehensive set of features that allow developers to manage their deployments with ease and confidence, ensuring that their services are always up and running as they should be. 
Whether you're just starting out with Kubernetes or are an experienced user, this API is the perfect tool for you to take control of your own infrastructure and get the most out of your deployments.


## Prerequisites

In order to run this application, you'll need the following prerequisites:
- A functioning kubernetes cluster
- Helm client installed on your local machine
- Kubectl installed and configured to interact with the kubernetes cluster

This application provides a Helm chart that can be easily installed on a kubernetes cluster, allowing you to effortlessly manage and deploy services within your cluster.
With the help of Helm and kubectl, this application provides an efficient and flexible way to manage your kubernetes cluster.

## Installation
1. Make sure you have a running kubernetes cluster.
2. Install the Helm client on your machine
3. Install kubectl.
4. Clone the repository containing the API solution and the Helm chart.
5. Navigate to the folder containing the Helm chart.
6. Use the following command to install the chart in your kubernetes cluster:
  ```shell
  helm install <release_name> .
  ```
7. Wait for the chart to be deployed in the cluster.
8. Verify the installation by checking the pods running in the namespace specified during the installation.

These steps will get you up and running with the API solution in no time. With the API and the UI, you will be able to deploy your services directly in the kubernetes cluster with ease.


### API Endpoints
- ###### GET /api/v1/namespaces/{namespace_name}/ingresses
  - Description: This endpoint retrieves the information about ingresses in a specific namespace. The response includes the name, namespace, and the host and path information for each ingress.
  - Path parameter: 
    - namespace_name (str): The name of the namespace to retrieve the ingresses from.
  - Response: A list of dictionaries, where each dictionary represents an ingress and its information. Each dictionary contains the following key-value pairs:
    - name (str): The name of the ingress.
    - namespace (str): The namespace the ingress belongs to.
    - rules (list of dictionaries): A list of dictionaries, where each dictionary represents a rule in the ingress. Each rule dictionary contains the following key-value pairs:
      - host (str): The host for the rule.
      - paths (list of dictionaries): A list of dictionaries, where each dictionary represents a path in the rule. Each path dictionary contains the following key-value pairs:
        - path (str): The path for the path.
        - service_name (str): The name of the service the path routes to.
Example response:
```json
[{"name": "ingress-1",        
  "namespace": "default",        
  "rules": [            
    {                
      "host": "example.com",                
      "paths": [                    
        {                        
          "path": "/api",                        
          "service_name": "service-1"
        },                    
        {                        
          "path": "/dashboard",                        
          "service_name": "service-2"
        }]
            }
        ]
    },
    {
        "name": "ingress-2",
        "namespace": "default",
        "rules": [
            {
                "host": "example.org",
                "paths": [
                    {
                        "path": "/",
                        "service_name": "service-3"
                    }
                ]
            }
        ]
    }
]

```
#### Endpoint: GET /api/v1/list-configmaps/{namespace}
- Description: This endpoint returns a list of all configmaps present in a specific namespace in the cluster.
- Input:
  - namespace: str: The name of the namespace for which the configmaps will be listed.
- Output: configmap: list: A list of dictionaries containing information about each configmap. The information includes:
  - name: str: The name of the configmap.
  - namespace: str: The namespace the configmap belongs to

#### Endpoint: GET /api/v1/get/{namespace}/configmap/{name}
- Parameters:
  - name (str): The name of the ConfigMap
  - namespace (str): The namespace in which the ConfigMap is stored.
- Return:
    - A dictionary containing the following key-value pairs:
      - configmap (List of dictionaries): A list of dictionaries containing information about each ConfigMap that matches the specified name and namespace. Each dictionary contains the following key-value pairs:
        - name (str): The name of the ConfigMap.
        - namespace (str): The namespace in which the ConfigMap is stored.
        - data (Dictionary): A dictionary of key-value pairs representing the data stored in the ConfigMap.
-Exception:
        - Raises a HTTPException with a status code of 500 and a detail message containing the error message if an exception occurs.

#### Endpoint: GET /api/v1/list-db-deployments
- Description: This endpoint retrieves the information of all deployments stored in the database.
- Request: GET /api/v1/list-db-deployments
- Response:
  - On Success:
```text
HTTP Status Code: 200 OK
Content-Type: application/json

{
    "deployments": [
        {
            ...
        },
        ...
    ]
}

```
  - On Failure:
```text
HTTP Status Code: 204 No Content
Content-Type: application/json

{
    "detail": "No namespaces found."
}

```
#### Endpoint: GET /api/v1/list-all-deployments
- This endpoint returns a list of all deployments in the Kubernetes cluster.
- Method: GET
- URL: /api/v1/list-all-deployments
- Request: None
- Response:
```text
200 (OK)
- Body: List of deployment dictionaries, with each dictionary containing:
    - name: deployment name
    - namespace: deployment namespace
    - replicas: number of replicas specified in deployment
    - status: number of replicas in the current deployment status
- 500 (Internal Server Error)
    - Body:
        - Details: a string describing the error encountered
```
#### Endpoint: POST /api/v1/create-deployment-by-manifest
- Description: This endpoint creates a deployment using a YAML file.
- Parameters:
  - file: a YAML file representing the deployment manifest
- Returns: A JSON object representing the status of the deployment creation.













## Usage


## Usage

To deploy a chart to a namespace, send a POST request to the /deploy/{namespace} endpoint with a JSON payload containing the chart name and chart repository URL.

Example payload:
```json
{
    "charts": [
        {
            "chart_name": "jenkins",
            "chart_repo_url": "https://charts.bitnami.com/bitnami",
            "release_name": "jenkins-backend",
            "provider": "bitnami"
        },
        {
            "chart_name": "wordpress",
            "chart_repo_url": "https://charts.bitnami.com/bitnami",
            "release_name": "wordpress-backend",
            "provider": "bitnami"
        }
    ]
    
}
```

## Delete All Namespaces
- Endpoint: `DELETE /namespaces/all`
- Description: This endpoint deletes all namespaces that are in the database and also delete them from the cluster
- Example:
    ```
    curl -X DELETE http://localhost:8000/namespaces/all
    ```
    ```json
    {"message":"All namespaces have been deleted."}
    ```

## Create namespace json format or yaml
```json
{
  "labels":{
     "app":"new-backend"
  }
}

```
### Update namespace payload sample:
```json
{
    "apiVersion": "v1",
    "kind": "Namespace",
    "metadata": {
        "name": "test-namespace",
        "labels": {
            "app": "test-backend"
        }
    }
}
```

### Create ingress payload:
```json
{
    "apiVersion": "extensions/v1beta1",
    "kind": "Ingress",
    "metadata": {
        "name": "example-ingress",
        "namespace": "default"
    },
    "spec": {
        "rules": [
            {
                "host": "example.com",
                "http": {
                    "paths": [
                        {
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": "example-service",
                                    "port": {
                                        "name": "http"
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
}
```

### Update ingress payload
```json
{
    "spec": {
        "rules": [
            {
                "host": "www.example.com",
                "http": {
                    "paths": [
                        {
                            "path": "/api/users",
                            "backend": {
                                "service": {
                                    "name": "user-service",
                                    "port": {
                                        "name": "http"
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
}
```
## Authors

* **Your Name** - *Initial work* - [cradules](https://github.com/cradules)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

### Documentation
[ kubernetes-python-client](https://k8s-python.readthedocs.io/en/latest/)
https://readthedocs.org/



