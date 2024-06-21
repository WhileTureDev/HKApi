# Database Schema

## Overview
This document describes the database schema used in the Kubernetes API Platform.

## Tables

### Users
- **users**:
  - id: Integer, primary key
  - username: String, unique, index
  - full_name: String, index
  - email: String, unique, index
  - hashed_password: String
  - created_at: DateTime
  - updated_at: DateTime
  - disabled: Boolean

### Projects
- **projects**:
  - id: Integer, primary key
  - name: String, unique, index
  - description: String
  - created_at: DateTime
  - updated_at: DateTime
  - owner_id: Integer, ForeignKey(users.id)

### Deployments
- **deployments**:
  - id: Integer, primary key
  - project: String
  - install_type: String
  - release_name: String
  - chart_name: String
  - chart_repo_url: String
  - namespace_id: Integer, ForeignKey(namespaces.id)
  - namespace_name: String
  - values: JSON
  - revision: Integer
  - active: Boolean
  - status: String
  - created_at: DateTime
  - updated_at: DateTime
  - owner_id: Integer, ForeignKey(users.id)

### Namespaces
- **namespaces**:
  - id: Integer, primary key
  - name: String, unique, index
  - project_id: Integer, ForeignKey(projects.id)
  - owner_id: Integer, ForeignKey(users.id)
  - created_at: DateTime
  - updated_at: DateTime

### Change Logs
- **change_logs**:
  - id: Integer, primary key
  - user_id: Integer, ForeignKey(users.id)
  - action: String, index
  - resource: String, index
  - resource_id: Integer, index
  - resource_name: String, index
  - project_name: String, index
  - timestamp: DateTime
  - details: String, nullable

### Audit Logs
- **audit_logs**:
  - id: Integer, primary key
  - user_id: Integer, ForeignKey(users.id)
  - action: String, index
  - resource: String, index
  - resource_id: Integer, index
  - resource_name: String, index
  - timestamp: DateTime
  - details: String, nullable
