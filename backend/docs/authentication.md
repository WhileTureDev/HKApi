# Authentication

## Overview
This document describes the authentication mechanism used in the Kubernetes API Platform.

## Token-Based Authentication
The API uses token-based authentication. Users must obtain an access token by providing their username and password.

### Obtain Access Token
- **Endpoint**: POST /token
- **Request Parameters**:
  - grant_type: password
  - username: {username}
  - password: {password}
- **Response**:
  - access_token: {token}
  - token_type: "bearer"

### Using Access Token
Include the access token in the `Authorization` header of each request:
Authorization: Bearer {access_token}

## Rate Limiting
Rate limiting is implemented to prevent abuse of the API. The rate limit can be configured using the `RATE_LIMIT` environment variable. The default value is `20/minute`.
