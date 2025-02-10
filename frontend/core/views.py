from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
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
                request.session['token'] = token_data.get('access_token')
                request.session['username'] = username  # Store username in session
                messages.success(request, 'Login successful!')
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
    # Get the token from session
    token = request.session.get('token')
    logger.debug(f"Token from session: {'Present' if token else 'Missing'}")
    if token:
        # Only log first 10 chars of token for security
        logger.debug(f"Token preview: {token[:10]}...")
    
    if not token:
        logger.warning("No token in session, redirecting to login")
        messages.error(request, 'Authentication token not found')
        return redirect('login')
    
    try:
        # Get user's projects
        logger.info(f"Fetching projects from {settings.API_URL}/api/v1/projects/")
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        logger.debug(f"Request headers: {headers}")
        
        projects_response = requests.get(
            f"{settings.API_URL}/api/v1/projects/",
            headers=headers
        )
        
        logger.debug(f"Projects response status: {projects_response.status_code}")
        logger.debug(f"Projects response headers: {dict(projects_response.headers)}")
        logger.debug(f"Projects response: {projects_response.text}")
        
        if projects_response.status_code == 200:
            projects = projects_response.json()
            logger.info(f"Found {len(projects)} projects")
            return render(request, 'core/dashboard.html', {'projects': projects})
        elif projects_response.status_code == 401:
            logger.warning("Token expired or invalid, redirecting to login")
            request.session.flush()
            messages.error(request, "Session expired. Please login again.")
            return redirect('login')
        else:
            error_detail = projects_response.json().get('detail', 'Unable to fetch projects')
            messages.error(request, f"API Error: {error_detail}")
            logger.error(f"Projects API error. Status: {projects_response.status_code}, Response: {projects_response.text}")
            return render(request, 'core/dashboard.html', {'projects': []})
        
    except requests.RequestException as e:
        messages.error(request, f"Unable to connect to API service: {str(e)}")
        logger.error(f"API service error: {str(e)}")
        return render(request, 'core/dashboard.html', {'projects': []})
    except Exception as e:
        logger.error(f"Unexpected error in dashboard: {str(e)}")
        messages.error(request, "An unexpected error occurred")
        return render(request, 'core/dashboard.html', {'projects': []})

@login_required
def create_project(request):
    if request.method == 'POST':
        try:
            # Get the token from session
            token = request.session.get('token')
            if not token:
                messages.error(request, 'Authentication token not found')
                return redirect('login')

            # Get project data from form
            name = request.POST.get('name')
            description = request.POST.get('description')

            # Create project via API
            response = requests.post(
                f"{settings.API_URL}/api/v1/projects/",
                json={
                    'name': name,
                    'description': description
                },
                headers={
                    'accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )

            if response.status_code == 201:
                messages.success(request, 'Project created successfully!')
            else:
                error_detail = response.json().get('detail', 'Failed to create project')
                messages.error(request, f"Error: {error_detail}")
                logger.error(f"Project creation failed. Status: {response.status_code}, Response: {response.text}")

        except requests.RequestException as e:
            messages.error(request, f"Unable to connect to API service: {str(e)}")
            logger.error(f"API service error: {str(e)}")
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
