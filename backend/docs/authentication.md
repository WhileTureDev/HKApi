# Authentication

## Overview
The platform uses OAuth2 with password flow for authentication. Users receive a token upon successful login, which is used to authenticate subsequent requests.

## Token Endpoint
- **POST /token**
  - Request: `{ "username": "string", "password": "string" }`
  - Response: `{ "access_token": "string", "token_type": "bearer" }`

## Securing Endpoints
All endpoints, except for the token endpoint, require an access token for authentication. Use the token received from the `/token` endpoint in the `Authorization` header as follows:
Authorization: Bearer <access_token>

## Token Validation
Tokens are validated using the secret key and the HS256 algorithm. The token must be included in the `Authorization` header of each request to protected endpoints.
