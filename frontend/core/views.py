from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import requests
from django.conf import settings
import logging
from django.views.decorators.csrf import csrf_protect

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
            return render(request, 'core/dashboard.html', {
                'projects': projects,
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
            response = requests.post(
                f"{settings.API_URL}/api/v1/projects/",
                json={
                    'name': name,
                    'description': description,
                    'owner_id': user_id  # Explicitly set the owner_id
                },
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )

            # Check response
            if response.status_code in [200, 201]:
                project_data = response.json()
                if project_data.get('owner_id') == user_id:
                    messages.success(request, f"Project '{name}' created successfully!")
                    logger.info(f"Project created with owner_id {user_id}: {name}")
                else:
                    logger.warning(f"Project created but owner_id mismatch. Expected: {user_id}, Got: {project_data.get('owner_id')}")
                    messages.success(request, f"Project '{name}' created successfully, but ownership verification pending.")
            else:
                # Verify if project was created despite error
                verify_response = requests.get(
                    f"{settings.API_URL}/api/v1/projects/",
                    headers={'Authorization': f'Bearer {token}'}
                )
                
                if verify_response.status_code == 200:
                    projects = verify_response.json()
                    # Check if our project exists in the latest projects with correct owner
                    latest_project = next((p for p in projects if p['name'] == name and p.get('owner_id') == user_id), None)
                    if latest_project:
                        messages.success(request, f"Project '{name}' was created successfully!")
                        logger.info(f"Project created despite error response. Owner ID verified: {user_id}")
                    else:
                        error_detail = response.json().get('detail', 'Unknown error occurred')
                        messages.error(request, f"Failed to create project: {error_detail}")
                        logger.error(f"Project creation failed. Status: {response.status_code}, Response: {response.text}")
                else:
                    error_detail = response.json().get('detail', 'Unknown error occurred')
                    messages.error(request, f"Failed to create project: {error_detail}")
                    logger.error(f"Project creation failed. Status: {response.status_code}, Response: {response.text}")

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

def logout_view(request):
    # Clear the session
    request.session.flush()
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')
