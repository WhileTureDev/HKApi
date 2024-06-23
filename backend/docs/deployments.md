# Deployment API Documentation

## Overview
The Deployment API provides endpoints to create, update, delete, list, and manage Kubernetes deployments within specific namespaces. This API ensures that only authorized users can perform actions on deployments.

## Endpoints

### List Deployments
**Endpoint:** `GET /deployments`

**Description:** List all deployments in a specific namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace from which to list deployments.

**Response:**
- `200 OK` on success with a JSON payload containing the list of deployments.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
GET /deployments?namespace=test-namespace

**Example Response:**
{
    "deployments": [
        {
            "name": "test-deployment",
            "namespace": "test-namespace",
            "replicas": 3,
            "available_replicas": 3,
            "updated_replicas": 3,
            "ready_replicas": 3,
            "conditions": [
                {
                    "type": "Available",
                    "status": "True",
                    "last_update_time": "2024-06-23T09:21:32+00:00",
                    "last_transition_time": "2024-06-23T09:21:32+00:00",
                    "reason": "MinimumReplicasAvailable",
                    "message": "Deployment has minimum availability."
                }
            ]
        }
    ]
}

### Get Deployment Details
**Endpoint:** `GET /deployment`

**Description:** Get the details of a specific deployment in a namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace of the deployment.
- `deployment_name` (query parameter, required): The name of the deployment.

**Response:**
- `200 OK` on success with a JSON payload containing the deployment details.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `404 Not Found` if the deployment does not exist.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
GET /deployment?namespace=test-namespace&deployment_name=test-deployment

**Example Response:**
{
    "name": "test-deployment",
    "namespace": "test-namespace",
    "replicas": 3,
    "available_replicas": 3,
    "updated_replicas": 3,
    "ready_replicas": 3,
    "conditions": [
        {
            "type": "Available",
            "status": "True",
            "last_update_time": "2024-06-23T09:21:32+00:00",
            "last_transition_time": "2024-06-23T09:21:32+00:00",
            "reason": "MinimumReplicasAvailable",
            "message": "Deployment has minimum availability."
        }
    ]
}

### Create Deployment
**Endpoint:** `POST /deployment`

**Description:** Create a new deployment in a specific namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace to create the deployment in.
- `deployment_name` (query parameter, required): The name of the deployment.
- `image` (query parameter, required): The image for the deployment.
- `yaml_file` (optional): The deployment manifest file in YAML format.

**Response:**
- `200 OK` on success with a JSON payload containing the deployment details.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
POST /deployment
{
    "namespace": "test-namespace",
    "deployment_name": "test-deployment",
    "image": "nginx"
}

**Example Response:**
{
    "name": "test-deployment",
    "namespace": "test-namespace",
    "status": "Pending",
    "containers": [
        {
            "name": "test-deployment",
            "image": "nginx"
        }
    ]
}

### Update Deployment
**Endpoint:** `PUT /deployment`

**Description:** Update an existing deployment in a specific namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace of the deployment.
- `deployment_name` (query parameter, required): The name of the deployment.
- `image` (query parameter, required): The new image for the deployment.

**Response:**
- `200 OK` on success with a JSON payload containing the updated deployment details.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `404 Not Found` if the deployment does not exist.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
PUT /deployment
{
    "namespace": "test-namespace",
    "deployment_name": "test-deployment",
    "image": "nginx:latest"
}

**Example Response:**
{
    "name": "test-deployment",
    "namespace": "test-namespace",
    "status": "Updated",
    "containers": [
        {
            "name": "test-deployment",
            "image": "nginx:latest"
        }
    ]
}

### Delete Deployment
**Endpoint:** `DELETE /deployment`

**Description:** Delete a specific deployment in a namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace of the deployment.
- `deployment_name` (query parameter, required): The name of the deployment.

**Response:**
- `200 OK` on success with a JSON payload confirming deletion.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `404 Not Found` if the deployment does not exist.
- `500 Internal Server Error` if an error occurs.

**Example Request:**
DELETE /deployment?namespace=test-namespace&deployment_name=test-deployment

**Example Response:**
{
    "message": "Deployment test-deployment deleted successfully from namespace test-namespace"
}

### Rollout Actions
**Endpoint:** `POST /deployment/rollout`

**Description:** Perform a rollout action (restart, rollback) on a deployment in a specific namespace.

**Parameters:**
- `namespace` (query parameter, required): The namespace of the deployment.
- `deployment_name` (query parameter, required): The name of the deployment.
- `action` (query parameter, required): The rollout action to perform (`restart`, `rollback`).
- `revision` (query parameter, optional): The revision number to rollback to (required for rollback action).

**Response:**
- `200 OK` on success with a JSON payload confirming the action.
- `403 Forbidden` if the user does not have permission to access the namespace.
- `404 Not Found` if the deployment does not exist.
- `500 Internal Server Error` if an error occurs.

**Example Request for Restart:**
POST /deployment/rollout
{
    "namespace": "test-namespace",
    "deployment_name": "test-deployment",
    "action": "restart"
}

**Example Request for Rollback:**
POST /deployment/rollout
{
    "namespace": "test-namespace",
    "deployment_name": "test-deployment",
    "action": "rollback",
    "revision": 2
}

**Example Response:**
{
    "message": "Rollout action restart performed successfully on deployment test-deployment in namespace test-namespace"
}

**Example Response for Rollback:**
{
    "message": "Rollout action rollback to revision 2 performed successfully on deployment test-deployment in namespace test-namespace"
}
