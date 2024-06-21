# Getting Started

## Overview
This guide will help you get started with the Kubernetes API Platform.

## Prerequisites
- Kubernetes cluster
- Helm installed
- Docker installed
- PostgreSQL database

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
   helm install helm-hkapi ./helm-hkapi

## Usage
Start the application and open your browser to `http://your-kubernetes-cluster-url`. You can use the API to manage projects, deployments, and namespaces.
