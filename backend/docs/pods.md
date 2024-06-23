# Pod API Documentation

## Overview
The Pod API provides endpoints to create, update, delete, list, and manage Kubernetes pods within specific namespaces. This API ensures that only authorized users can perform actions on pods.

## Endpoints

### List Pods
**Endpoint:** `GET /pods`

**Description:** List all pods in a specific namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace from which to list pods.

**Response:**
- `200 OK` on success with a JSON payload containing the list of pods.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
GET /pods?namespace=test-namespace

**Example Response:**
{
    "pods": [
        {
            "name": "test-pod",
            "namespace": "test-namespace",
            "status": "Running",
            "node_name": "kube-node",
            "start_time": "2024-06-23T09:21:32+00:00",
            "containers": [
                {
                    "name": "test-pod",
                    "image": "nginx"
                }
            ],
            "host_ip": "192.168.1.62",
            "pod_ip": "10.1.42.163"
        }
    ]
}

### Get Pod Details
**Endpoint:** `GET /pod`

**Description:** Get the details of a specific pod in a namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace of the pod.
- `pod_name` (query parameter, required): The name of the pod.

**Response:**
- `200 OK` on success with a JSON payload containing the pod details.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `404 Not Found` if the pod does not exist.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
GET /pod?namespace=test-namespace&pod_name=test-pod

**Example Response:**
{
    "name": "test-pod",
    "namespace": "test-namespace",
    "status": "Running",
    "node_name": "kube-node",
    "start_time": "2024-06-23T09:21:32+00:00",
    "containers": [
        {
            "name": "test-pod",
            "image": "nginx",
            "ready": true,
            "restart_count": 0
        }
    ],
    "host_ip": "192.168.1.62",
    "pod_ip": "10.1.42.163"
}

### Create Pod
**Endpoint:** `POST /pod`

**Description:** Create a new pod in a specific namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace to create the pod in.
- `pod_name` (query parameter, required): The name of the pod.
- `image` (query parameter, required): The image for the pod.
- `yaml_file` (optional): The pod manifest file in YAML format.

**Response:**
- `200 OK` on success with a JSON payload containing the pod details.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
POST /pod
{
    "namespace": "test-namespace",
    "pod_name": "test-pod",
    "image": "nginx"
}

**Example Response:**
{
    "name": "test-pod",
    "namespace": "test-namespace",
    "status": "Pending",
    "containers": [
        {
            "name": "test-pod",
            "image": "nginx"
        }
    ]
}

### Update Pod
**Endpoint:** `PUT /pod`

**Description:** Update an existing pod in a specific namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace of the pod.
- `pod_name` (query parameter, required): The name of the pod.
- `image` (query parameter, required): The new image for the pod.

**Response:**
- `200 OK` on success with a JSON payload containing the updated pod details.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `404 Not Found` if the pod does not exist.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
PUT /pod
{
    "namespace": "test-namespace",
    "pod_name": "test-pod",
    "image": "nginx:latest"
}

**Example Response:**
{
    "name": "test-pod",
    "namespace": "test-namespace",
    "status": "Updated",
    "containers": [
        {
            "name": "test-pod",
            "image": "nginx:latest"
        }
    ]
}

### Delete Pod
**Endpoint:** `DELETE /pod`

**Description:** Delete a specific pod in a namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace of the pod.
- `pod_name` (query parameter, required): The name of the pod.

**Response:**
- `200 OK` on success with a JSON payload confirming deletion.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `404 Not Found` if the pod does not exist.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
DELETE /pod?namespace=test-namespace&pod_name=test-pod

**Example Response:**
{
    "message": "Pod test-pod deleted successfully from namespace test-namespace"
}

### Get Pod Logs
**Endpoint:** `GET /pod/logs`

**Description:** Get the logs of a specific pod in a namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace of the pod.
- `pod_name` (query parameter, required): The name of the pod.
- `container_name` (query parameter, optional): The name of the container. If not specified, logs from the first container are returned.

**Response:**
- `200 OK` on success with a plain text payload containing the pod logs.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `404 Not Found` if the pod or container does not exist.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
GET /pod/logs?namespace=test-namespace&pod_name=test-pod&container_name=test-container

**Example Response:**
"Logs from container test-container in pod test-pod"
