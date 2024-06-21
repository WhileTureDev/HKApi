# API Endpoints

## Overview
This document provides an overview of the available API endpoints.

### Authentication
- **POST /token**: Obtain an access token.
  - Request:
    - grant_type: password
    - username: {username}
    - password: {password}
  - Response:
    - access_token: {token}
    - token_type: "bearer"

### Users
- **POST /users/**: Create a new user.
- **GET /users/me**: Get details of the current user.
- **POST /users/{user_id}/roles/{role_id}**: Assign a role to a user.

### Projects
- **GET /projects/**: List all projects.
- **POST /projects/**: Create a new project.
- **GET /projects/{project_id}**: Get details of a specific project.
- **PUT /projects/{project_id}**: Update a project.
- **DELETE /projects/{project_id}**: Delete a project.

### Deployments
- **POST /helm/releases**: Create a new Helm release.
- **DELETE /helm/releases**: Delete a Helm release.
- **GET /helm/releases**: List Helm releases.
- **GET /helm/releases/values**: Get values of a Helm release.
- **POST /helm/releases/rollback**: Rollback a Helm release.
- **GET /helm/releases/status**: Get status of a Helm release.
- **GET /helm/releases/history**: Get history of a Helm release.
- **GET /helm/releases/notes**: Get notes of a Helm release.
- **GET /helm/releases/export**: Export values of a Helm release.

### Admin
- **GET /admin/helm/releases/all**: List all Helm releases (admin only).
- **GET /admin/audit_logs**: Get audit logs (admin only).

### Changelogs
- **GET /changelogs**: List all change logs.
- **GET /changelogs/user/{user_id}**: Get change logs for a specific user.
- **GET /changelogs/resource/{resource}/{resource_name}**: Get change logs for a specific resource.

### Healthcheck
- **GET /**: Health check endpoint.
