# Documentation for `create_release` Function

## Overview
The `create_release` function is an HTTP POST endpoint that facilitates the creation of a Helm release in a Kubernetes cluster. It supports providing chart values through JSON or file uploads and handles additional functionality such as namespace management, repository setup, and Helm chart deployment.

---

## Endpoint
**URL**: `/helm/releases`  
**Method**: POST

---

## Parameters

### Query Parameters

| **Parameter**    | **Type**         | **Required** | **Description**                                                          | **Example**                          |
|------------------|------------------|--------------|--------------------------------------------------------------------------|--------------------------------------|
| `release_name`   | `str`            | Yes          | The name of the Helm release to be created.                              | `wordpress-test`                     |
| `chart_name`     | `str`            | Yes          | The name of the Helm chart to deploy.                                    | `wordpress`                          |
| `chart_repo_url` | `str`            | Yes          | The URL of the Helm chart repository.                                    | `https://charts.bitnami.com/bitnami` |
| `namespace`      | `str`            | Yes          | The namespace in which to create the Helm release.                       | `wordpress-namespace`                |
| `project`        | `Optional[str]`  | No           | The name of the project to associate with the release.                   | `my-project`                         |
| `values`         | `Optional[str]`  | No           | Chart values in JSON format. Overrides default chart values if provided. | `{"ingress": {"enabled": true}}`     |
| `version`        | `Optional[str]`  | No           | The version of the Helm chart to deploy.                                 | `1.2.3`                              |
| `debug`          | `Optional[bool]` | No           | Flag to enable debug mode during deployment.                             | `true`                               |

### File Parameters

| **Parameter** | **Type**     | **Required** | **Description**                                                                             | **Example**             |
|---------------|--------------|--------------|---------------------------------------------------------------------------------------------|-------------------------|
| `values_file` | `UploadFile` | No           | A YAML file containing Helm chart values. Overrides both defaults and `values` if provided. | `wordpress-values.yaml` |

### Dependency Parameters

These parameters are injected by the FastAPI `Depends` mechanism:

| **Parameter**        | **Type**    | **Description**                                             |
|----------------------|-------------|-------------------------------------------------------------|
| `db`                 | `Session`   | Database session dependency.                                |
| `current_user`       | `UserModel` | The currently authenticated user.                           |
| `current_user_roles` | `List[str]` | List of roles assigned to the currently authenticated user. |

---

## Functionality

### Step-by-Step Process

1. **Validate User Permissions**
   - If the user is an admin, they can access all projects and namespaces.
   - Non-admin users are validated against their ownership of the project and namespace.

2. **Parse Chart Values**
   - If `values` is provided, it is parsed as JSON.
   - If `values_file` is uploaded, it is saved temporarily and loaded as YAML.

3. **Namespace Management**
   - If the specified namespace does not exist, it is created and associated with the project.

4. **Helm Repository Setup**
   - Extracts the repository name from `chart_repo_url`.
   - If the repository is not found in the database, it is added and also added to Helm.

5. **Deploy the Helm Chart**
   - The Helm chart is deployed using the combined function `deploy_helm_chart_combined`.
   - The deployment is associated with a revision.

6. **Record Deployment**
   - A new deployment record is created in the database with all relevant details.

7. **Log Changes**
   - Logs the deployment operation with comprehensive details for auditing.

---

## Example Usage

### JSON-Based Request

```bash
curl -X POST "http://your-api-url/helm/releases" \
  -H "Content-Type: application/json" \
  -d '{
        "release_name": "wordpress-test",
        "chart_name": "wordpress",
        "chart_repo_url": "https://charts.bitnami.com/bitnami",
        "namespace": "wordpress-namespace",
        "project": "my-project",
        "values": "{\"ingress\": {\"enabled\": true, \"hostname\": \"wordpress-test.dailytoolset.com\"}, \"replicaCount\": 2}",
        "version": "latest",
        "debug": true
      }'
```

### File-Based Request

1. Create a `values.yaml` file:

```yaml
ingress:
  enabled: true
  hostname: wordpress-test.dailytoolset.com
replicaCount: 2
```

2. Upload the file:

```bash
curl -X POST "http://your-api-url/helm/releases" \
  -F "release_name=wordpress-test" \
  -F "chart_name=wordpress" \
  -F "chart_repo_url=https://charts.bitnami.com/bitnami" \
  -F "namespace=wordpress-namespace" \
  -F "project=my-project" \
  -F "values_file=@values.yaml" \
  -F "version=latest" \
  -F "debug=true"
```

---

## Return Value

### Success
On successful execution, the function returns a `DeploymentSchema` object:

```json
{
  "id": 1,
  "release_name": "wordpress-test",
  "chart_name": "wordpress",
  "namespace_name": "wordpress-namespace",
  "project": "my-project",
  "values": {
    "ingress": {
      "enabled": true,
      "hostname": "wordpress-test.dailytoolset.com"
    },
    "replicaCount": 2
  },
  "revision": 1,
  "status": "deployed",
  "created_at": "2025-01-19T00:00:00",
  "updated_at": "2025-01-19T00:00:00"
}
```

### Error
Returns an HTTP error code with a detailed message. Examples:
- `400 Bad Request` if parameters are invalid.
- `500 Internal Server Error` if the Helm deployment fails.

---

## Additional Notes
- Temporary files created for `values_file` are automatically deleted after processing.
- Ensure that the Helm repository is accessible from the environment where the API runs.
- Admin users have unrestricted access, while others require ownership validation.

