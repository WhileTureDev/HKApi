# How  to use Postman to test the API


## Overview
For testing the API, you can use Postman to send requests to the server. Postman is a popular API client that makes it easy to test and debug APIs. You can use it to send requests to the server and view the responses.


## Installation
1. Download and install Postman from the [official website](https://www.postman.com/downloads/).

## Linux
For linux users, you can install Postman using the following commands:

```bash
sudo snap install postman
```

## Usage

Pre-requisites:
- The API is running and accessible.
- Create a user account using the API.
- URL: {{BASE_URL}}/users
- Method: POST
- Headers: Content-Type: application/json
- Body: 
```json
{
  "username": "user",
  "full_name": "Full Name",
  "email": "email@example.com",
  "disabled": false,
  "password": "password"
}
```

1. Open and create a user for the API. The body of the request should contain the following fields:

raw 
```json
{
  "username": "user",
  "full_name": "Full Name",
  "email": "email@example.com",
  "disabled": false,
  "password": "password"
}
```
2. Create a script that will grab the access token from the response and store it in an environment variable. This will allow you to use the access token in subsequent requests.

```javascript
pm.test("Update access_token", function () {
    try {
        // 1. Parse JSON Response:
        const responseJson = pm.response.json();

        // 2. Extract access_token:
        const accessToken = responseJson.access_token; 

        // 3. Set Environment Variable:
        pm.environment.set("access_token", accessToken);

        // 4. Optional Logging (for debugging):
        console.log("Access token updated:", accessToken); 
    } catch (error) {
        console.error("Error updating access token:", error);
        // Handle the error appropriately (e.g., throw an error, display a message)
    }
});

```

This will create the `access_token` environment variable that you can use in subsequent requests.
