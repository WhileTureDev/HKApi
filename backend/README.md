# Kubernetes API Platform

## Overview
This project is a Kubernetes API platform that allows developers to create and manage temporary environments in a Kubernetes cluster. It provides a user interface for deploying and managing Helm charts.

## Installation
1. Clone the repository:
   ```shell
   git clone https://github.com/your-repo/kubernetes-api-platform.git
   cd kubernetes-api-platform
   ```

2. Navigate to the backend directory:
   ```shell
   cd backend
   ```

3. Build the Docker image:
   ```shell
   docker build -t your-image-name .
   ```

4. Update the Helm chart values:
   - Open `backend/helm-hkapi/values.yaml` and update the following values:
     ```yaml
     DATABASE_HOST: "postgres-postgresql"
     ACCESS_TOKEN_EXPIRE_MINUTES: "60"
     ```

5. Deploy the API using Helm:
   ```shell
   helm install helm-hkapi ./helm-hkapi
   ```

## Usage
Start the application and open your browser to `http://your-kubernetes-cluster-url`. You can use the API to manage projects, deployments, and namespaces.

## Documentation
- [Getting Started](docs/getting_started.md)
- [API Endpoints](docs/api_endpoints.md)
- [Authentication](docs/authentication.md)
- [Database Schema](docs/database_schema.md)
- [Helm Integration](docs/helm_integration.md)
- [Contributing](docs/contributing.md)
- [License](docs/license.md)
