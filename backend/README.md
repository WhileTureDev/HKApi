# Kubernetes API Platform


## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [License](#license)
- [Contributing](#contributing)
- [Support](#support)
- [Acknowledgements](#acknowledgements)
- [Authors](#authors)
- [Feedback](#feedback)
- [Resources](#resources)
- [FAQ](#faq)
- [Changelog](#changelog)
- [Roadmap](#roadmap)
- [Security](#security)
- [Postman](docs/postman.md)
- [API Endpoints](docs/api_endpoints.md)
- [Authentication](docs/authentication.md)
- [Database Schema](docs/database_schema.md)
- [Helm Integration](docs/helm_integration.md)
- [Pods](docs/pods.md)
- [Deployments](docs/deployments.md)
- [Contributing](docs/contributing.md)
- [Getting Started](docs/getting_started.md)
- [Create Release](docs/create_release.md)
## Overview
This project is a Kubernetes API platform that allows developers to create and manage temporary environments in a Kubernetes cluster. It provides a user interface for deploying and managing Helm charts.

## Installation
1. Clone the repository:
   git clone https://github.com/your-repo/kubernetes-api-platform.git
   cd kubernetes-api-platform

2. Navigate to the backend directory:
   cd backend

3. Build the Docker image:
   docker build -t your-image-name .

4. Update the Helm chart values:
   - Open `backend/helm-hkapi/values.yaml` and update the following values:
     DATABASE_HOST: "postgres-postgresql"
     ACCESS_TOKEN_EXPIRE_MINUTES: "60"

5. Set the required environment variables:
   - You can set these in your deployment environment configuration.
     POSTGRES_PASSWORD=your_postgres_password
     ADMIN_PASSWORD=your_admin_password
     RATE_LIMIT=20/minute

6. Deploy the API using Helm:
   helm install helm-hkapi ./helm-hkapi --namespace hkapi

## Usage
Start the application and open your browser to `http://your-kubernetes-cluster-url`. You can use the API to manage projects, deployments, and namespaces.



## Postman
For testing the API, you can use Postman to send requests to the server. Postman is a popular API client that makes it easy to test and debug APIs. You can use it to send requests to the server and view the responses.

