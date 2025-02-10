from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import requests
from django.conf import settings
import logging
from django.views.decorators.csrf import csrf_protect
import random
import json
import yaml
from django.http import JsonResponse
from datetime import datetime

logger = logging.getLogger(__name__)

# Create your views here.

def index(request):
    return render(request, 'core/index.html')

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Clear any existing session data
            request.session.flush()
            
            response = requests.post(
                f"{settings.API_URL}/api/v1/auth/token",
                data={
                    'username': username,
                    'password': password,
                    'grant_type': 'password'
                },
                headers={
                    'accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                # Store token and username in session
                request.session['token'] = token_data.get('access_token')
                request.session['username'] = username
                
                # Create or get Django user for session auth
                user, created = User.objects.get_or_create(username=username)
                if created:
                    user.save()
                login(request, user)
                
                messages.success(request, 'Login successful!')
                logger.info(f"User {username} logged in successfully")
                
                # Check if there's a next parameter
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                error_detail = response.json().get('detail', 'Invalid credentials')
                messages.error(request, f"Login failed: {error_detail}")
                logger.error(f"Login failed for user {username}. Status: {response.status_code}, Response: {response.text}")
                request.session.flush()
                
        except requests.RequestException as e:
            messages.error(request, f"Unable to connect to API service: {str(e)}")
            logger.error(f"API service error: {str(e)}")
            request.session.flush()
        except Exception as e:
            messages.error(request, "An unexpected error occurred")
            logger.error(f"Unexpected error in login: {str(e)}")
            request.session.flush()
            
    return render(request, 'core/login.html')

@csrf_protect
def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validate passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'core/signup.html')

        try:
            # Create user via API
            response = requests.post(
                f"{settings.API_URL}/api/v1/users/",
                json={
                    'username': username,
                    'full_name': full_name,
                    'email': email,
                    'password': password,
                    'disabled': False
                },
                headers={'accept': 'application/json', 'Content-Type': 'application/json'}
            )

            if response.status_code in [200, 201]:  # Success
                logger.info(f"User created successfully: {username}")
                messages.success(request, "Account created successfully! Please log in.")
                return redirect('login')
            else:
                error_detail = response.json().get('detail', 'Failed to create account')
                messages.error(request, f"Error: {error_detail}")
                logger.error(f"User creation failed. Status: {response.status_code}, Response: {response.text}")

        except requests.RequestException as e:
            messages.error(request, f"Unable to connect to API service: {str(e)}")
            logger.error(f"API service error: {str(e)}")
        except Exception as e:
            messages.error(request, "An unexpected error occurred")
            logger.error(f"Unexpected error in signup: {str(e)}")

    return render(request, 'core/signup.html')

@login_required
def dashboard(request):
    token = request.session.get('token')
    if not token:
        messages.error(request, "Authentication token not found. Please login again.")
        return redirect('login')

    try:
        # Get user information first
        user_response = requests.get(
            f"{settings.API_URL}/api/v1/users/me",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if user_response.status_code != 200:
            messages.error(request, "Failed to get user information")
            return redirect('login')

        user_data = user_response.json()
        user_id = user_data.get('id')

        # Get projects filtered by owner_id
        response = requests.get(
            f"{settings.API_URL}/api/v1/projects/",
            headers={'Authorization': f'Bearer {token}'},
            params={'owner_id': user_id}  # Add filter for owner_id
        )

        if response.status_code == 200:
            projects = response.json()
            logger.debug(f"Projects response: {projects}")
            
            # Convert date strings to datetime objects
            for project in projects:
                if 'created_at' in project:
                    try:
                        project['created_at'] = datetime.strptime(project['created_at'], "%Y-%m-%dT%H:%M:%S.%f")
                    except ValueError as e:
                        logger.error(f"Date conversion error: {str(e)}")
                        messages.error(request, "Invalid date format in project data.")
                if 'updated_at' in project:
                    try:
                        project['updated_at'] = datetime.strptime(project['updated_at'], "%Y-%m-%dT%H:%M:%S.%f")
                    except ValueError as e:
                        logger.error(f"Date conversion error: {str(e)}")
                        messages.error(request, "Invalid date format in project data.")
                for namespace in project.get('namespaces', []):
                    if 'created_at' in namespace:
                        try:
                            namespace['created_at'] = datetime.strptime(namespace['created_at'], "%Y-%m-%dT%H:%M:%S.%f")
                        except ValueError as e:
                            logger.error(f"Date conversion error: {str(e)}")
                            messages.error(request, "Invalid date format in namespace data.")
                    if 'updated_at' in namespace:
                        try:
                            namespace['updated_at'] = datetime.strptime(namespace['updated_at'], "%Y-%m-%dT%H:%M:%S.%f")
                        except ValueError as e:
                            logger.error(f"Date conversion error: {str(e)}")
                            messages.error(request, "Invalid date format in namespace data.")
            
            return render(request, 'core/dashboard.html', {
                'projects': projects,
                'api_url': settings.API_URL,
                'request': request,  # Pass request to template for token access
                'username': request.session.get('username')
            })
        else:
            error_detail = response.json().get('detail', 'Failed to fetch projects')
            messages.error(request, f"Error: {error_detail}")
            logger.error(f"Failed to fetch projects. Status: {response.status_code}, Response: {response.text}")
            return render(request, 'core/dashboard.html', {'projects': []})

    except requests.RequestException as e:
        messages.error(request, f"Failed to connect to API: {str(e)}")
        logger.error(f"API connection error: {str(e)}")
        return render(request, 'core/dashboard.html', {'projects': []})
    except Exception as e:
        messages.error(request, "An unexpected error occurred")
        logger.error(f"Unexpected error in dashboard: {str(e)}")
        return render(request, 'core/dashboard.html', {'projects': []})

@login_required
def create_project(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        token = request.session.get('token')
        username = request.session.get('username')

        if not token:
            messages.error(request, "Authentication token not found. Please login again.")
            return redirect('login')

        try:
            # First get the current user's ID
            user_response = requests.get(
                f"{settings.API_URL}/api/v1/users/me",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if user_response.status_code != 200:
                messages.error(request, "Failed to get user information")
                logger.error(f"Failed to get user info. Status: {user_response.status_code}, Response: {user_response.text}")
                return redirect('dashboard')

            user_data = user_response.json()
            user_id = user_data.get('id')
            
            if not user_id:
                messages.error(request, "Could not determine user ID")
                logger.error(f"No user ID in response: {user_data}")
                return redirect('dashboard')

            # Create project with explicit owner_id
            project_response = requests.post(
                f"{settings.API_URL}/api/v1/projects/",
                json={
                    'name': name,
                    'description': description,
                    'owner_id': user_id
                },
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )

            # Check project creation response
            if project_response.status_code in [200, 201]:
                project_data = project_response.json()
                project_id = project_data.get('id')

                # Generate unique namespace name
                unique_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
                namespace_name = f"{username}-{name}-{unique_id}".lower().replace(' ', '-').replace('_', '-')

                # Create namespace with correct endpoint and payload
                namespace_response = requests.post(
                    f"{settings.API_URL}/api/v1/namespaces/create",
                    json={
                        'name': namespace_name,
                        'project_id': project_id
                    },
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }
                )

                if namespace_response.status_code in [200, 201]:
                    messages.success(request, f"Project '{name}' created successfully with namespace '{namespace_name}'!")
                    logger.info(f"Project and namespace created: {name}, {namespace_name}")
                else:
                    messages.warning(request, f"Project created but namespace creation failed. Please try adding a namespace manually.")
                    logger.error(f"Namespace creation failed. Status: {namespace_response.status_code}, Response: {namespace_response.text}")
            else:
                error_detail = project_response.json().get('detail', 'Unknown error occurred')
                messages.error(request, f"Failed to create project: {error_detail}")
                logger.error(f"Project creation failed. Status: {project_response.status_code}, Response: {project_response.text}")

        except requests.RequestException as e:
            messages.error(request, f"Failed to connect to API: {str(e)}")
            logger.error(f"API connection error: {str(e)}")
        except Exception as e:
            messages.error(request, "An unexpected error occurred")
            logger.error(f"Unexpected error in create_project: {str(e)}")

    return redirect('dashboard')

@login_required
def delete_project(request, project_id):
    if request.method == 'POST':
        try:
            # Get the token from session
            token = request.session.get('token')
            if not token:
                messages.error(request, 'Authentication token not found')
                return redirect('login')

            # Delete project via API
            response = requests.delete(
                f"{settings.API_URL}/api/v1/projects/{project_id}",
                headers={
                    'accept': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )

            if response.status_code == 204:  # No Content
                messages.success(request, 'Project deleted successfully!')
            else:
                error_detail = response.json().get('detail', 'Failed to delete project')
                messages.error(request, f"Error: {error_detail}")
                logger.error(f"Project deletion failed. Status: {response.status_code}, Response: {response.text}")

        except requests.RequestException as e:
            messages.error(request, f"Unable to connect to API service: {str(e)}")
            logger.error(f"API service error: {str(e)}")
        except Exception as e:
            messages.error(request, "An unexpected error occurred")
            logger.error(f"Unexpected error in delete_project: {str(e)}")

    return redirect('dashboard')

@login_required
def create_namespace(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        project_id = request.POST.get('project_id')
        token = request.session.get('token')

        if not token:
            messages.error(request, "Authentication token not found. Please login again.")
            return redirect('login')

        try:
            # Get user information first
            user_response = requests.get(
                f"{settings.API_URL}/api/v1/users/me",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if user_response.status_code != 200:
                messages.error(request, "Failed to get user information")
                return redirect('dashboard')

            user_data = user_response.json()
            user_id = user_data.get('id')

            # Create namespace
            response = requests.post(
                f"{settings.API_URL}/api/v1/namespaces/create",
                json={
                    'name': name,
                    'project_id': project_id
                },
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )

            if response.status_code in [200, 201]:
                messages.success(request, f"Namespace '{name}' created successfully!")
                logger.info(f"Namespace created: {name}")
            else:
                error_detail = response.json().get('detail', 'Unknown error occurred')
                messages.error(request, f"Failed to create namespace: {error_detail}")
                logger.error(f"Namespace creation failed. Status: {response.status_code}, Response: {response.text}")

        except requests.RequestException as e:
            messages.error(request, f"Failed to connect to API: {str(e)}")
            logger.error(f"API connection error: {str(e)}")
        except Exception as e:
            messages.error(request, "An unexpected error occurred")
            logger.error(f"Unexpected error in create_namespace: {str(e)}")

    return redirect('dashboard')

@login_required
def delete_namespace(request, namespace_id):
    if request.method == 'POST':
        token = request.session.get('token')
        if not token:
            messages.error(request, "Authentication token not found. Please login again.")
            return redirect('login')

        try:
            # Delete namespace with correct endpoint
            response = requests.delete(
                f"{settings.API_URL}/api/v1/namespaces/delete/{namespace_id}",
                headers={'Authorization': f'Bearer {token}'}
            )

            # Expect 204 No Content for successful deletion
            if response.status_code == 204:
                messages.success(request, "Namespace deleted successfully!")
                logger.info(f"Namespace {namespace_id} deleted successfully")
            else:
                try:
                    error_detail = response.json().get('detail', 'Unknown error occurred')
                except ValueError:
                    error_detail = 'Unknown error occurred'
                messages.error(request, f"Failed to delete namespace: {error_detail}")
                logger.error(f"Namespace deletion failed. Status: {response.status_code}, Response: {response.text}")

        except requests.RequestException as e:
            messages.error(request, f"Failed to connect to API: {str(e)}")
            logger.error(f"API connection error: {str(e)}")
        except Exception as e:
            messages.error(request, "An unexpected error occurred")
            logger.error(f"Unexpected error in delete_namespace: {str(e)}")

    return redirect('dashboard')

@login_required
def create_deployment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get form data
        namespace_name = request.POST.get('namespace_name')
        deployment_name = request.POST.get('release_name')
        yaml_config = request.POST.get('values')
        
        # Basic validation
        if not all([namespace_name, deployment_name, yaml_config]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Validate YAML format
        try:
            import yaml
            yaml.safe_load(yaml_config)
        except yaml.YAMLError as e:
            return JsonResponse({'error': f'Invalid YAML format: {str(e)}'}, status=400)
        
        # Make API request to create deployment
        api_url = f'{settings.API_BASE_URL}/api/v1/deployments'
        headers = {
            'Authorization': f'Bearer {request.session.get("access_token")}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'namespace': namespace_name,
            'deployment_name': deployment_name,
            'yaml_file': yaml_config
        }
        
        response = requests.post(api_url, json=data, headers=headers, verify=False)
        
        if response.status_code == 201:
            messages.success(request, 'Deployment created successfully')
            return JsonResponse({'message': 'Deployment created successfully'})
        else:
            error_msg = response.json().get('detail', 'Failed to create deployment')
            return JsonResponse({'error': error_msg}, status=response.status_code)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def create_helm_release(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Get query parameters from request
        release_name = request.GET.get('release_name')
        chart_name = request.GET.get('chart_name')
        chart_repo_url = request.GET.get('chart_repo_url')
        namespace = request.GET.get('namespace')
        project = request.GET.get('project')
        version = request.GET.get('version')
        debug = request.GET.get('debug', 'false')

        # Get values from request body
        data = json.loads(request.body)
        values = data.get('values', {})

        # Validate required fields
        if not all([release_name, chart_name, chart_repo_url, namespace, project]):
            logger.error("Missing required fields")
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        logger.info(f"Creating Helm release with params: release_name={release_name}, chart_name={chart_name}, namespace={namespace}")

        # Make API request to create Helm release
        response = requests.post(
            f"{settings.API_URL}/api/v1/helm/releases",
            params={
                'release_name': release_name,
                'chart_name': chart_name,
                'chart_repo_url': chart_repo_url,
                'namespace': namespace,
                'project': project,
                'version': version,
                'debug': debug
            },
            json={'values': values},
            headers={'Authorization': f"Bearer {request.session.get('token')}"}
        )

        response_data = response.json()
        if response.status_code == 201:
            logger.info(f"Successfully created Helm release {release_name}")
            return JsonResponse(response_data)
        else:
            logger.error(f"Failed to create Helm release: {response_data}")
            return JsonResponse(response_data, status=response.status_code)

    except Exception as e:
        logger.error(f"Error creating Helm release: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def list_helm_releases(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        namespace = request.GET.get('namespace')
        params = {'namespace': namespace} if namespace else {}

        response = requests.get(
            f"{settings.API_URL}/api/v1/helm/releases",
            params=params,
            headers={'Authorization': f"Bearer {request.session.get('token')}"}
        )

        if response.status_code == 200:
            return JsonResponse(response.json(), safe=False)
        else:
            return JsonResponse({'error': response.json().get('detail', 'Failed to list releases')}, 
                              status=response.status_code)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_helm_release(request, release_name):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        namespace = request.GET.get('namespace')
        if not namespace:
            return JsonResponse({'error': 'Namespace is required'}, status=400)

        # Get release status
        status_response = requests.get(
            f"{settings.API_URL}/api/v1/helm/releases/{release_name}/status",
            params={'namespace': namespace},
            headers={'Authorization': f"Bearer {request.session.get('token')}"}
        )

        # Get release values
        values_response = requests.get(
            f"{settings.API_URL}/api/v1/helm/releases/{release_name}/values",
            params={'namespace': namespace},
            headers={'Authorization': f"Bearer {request.session.get('token')}"}
        )

        if status_response.status_code == 200 and values_response.status_code == 200:
            return JsonResponse({
                'status': status_response.json(),
                'values': values_response.json()
            })
        else:
            error_response = status_response if status_response.status_code != 200 else values_response
            return JsonResponse({'error': error_response.json().get('detail', 'Failed to get release details')}, 
                              status=error_response.status_code)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_helm_release(request, release_name):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        namespace = request.GET.get('namespace')
        if not namespace:
            return JsonResponse({'error': 'Namespace is required'}, status=400)

        response = requests.delete(
            f"{settings.API_URL}/api/v1/helm/releases/{release_name}",
            params={'namespace': namespace},
            headers={'Authorization': f"Bearer {request.session.get('token')}"}
        )

        if response.status_code == 204:
            return JsonResponse({'message': 'Release deleted successfully'})
        else:
            return JsonResponse({'error': response.json().get('detail', 'Failed to delete release')}, 
                              status=response.status_code)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def rollback_helm_release(request, release_name):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        namespace = data.get('namespace')
        revision = data.get('revision')
        options = data.get('options', {})

        if not all([namespace, revision]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        response = requests.post(
            f"{settings.API_URL}/api/v1/helm/releases/{release_name}/rollback",
            params={
                'namespace': namespace,
                'revision': revision
            },
            json=options,
            headers={'Authorization': f"Bearer {request.session.get('token')}"}
        )

        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'error': response.json().get('detail', 'Failed to rollback release')}, 
                              status=response.status_code)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def logout_view(request):
    # Clear the session
    request.session.flush()
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')
