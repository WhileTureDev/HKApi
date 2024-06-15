
### docs/api_endpoints.md

```markdown
# API Endpoints

## Authentication
- **POST /token**
  - Request: `{ "username": "string", "password": "string" }`
  - Response: `{ "access_token": "string", "token_type": "bearer" }`

## User Management
- **GET /users/me**
  - Response: `UserSchema`

- **POST /users/**
  - Request: `UserCreate`
  - Response: `UserSchema`

## Project Management
- **GET /projects**
  - Response: `List[ProjectSchema]`

- **POST /projects**
  - Request: `ProjectCreate`
  - Response: `ProjectSchema`

## Deployment Management
- **POST /helm/releases**
  - Request: `DeploymentCreate`
  - Response: `Deployment`

- **DELETE /helm/releases**
  - Query Parameters:
    - `release_name`: `string`
    - `namespace`: `string`
  - Response: `Deployment`
