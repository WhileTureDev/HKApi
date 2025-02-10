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
    # Clear any existing session data
    request.session.flush()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate with the FastAPI backend
        try:
            logger.info(f"Attempting to authenticate user {username} with API at {settings.API_URL}")
            response = requests.post(
                f"{settings.API_URL}/api/v1/token",
                data={
                    'username': username,
                    'password': password,
                    'grant_type': 'password',
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'accept': 'application/json'
                }
            )
            
            logger.debug(f"Auth response status: {response.status_code}")
            logger.debug(f"Auth response: {response.text}")
            
            if response.status_code == 200:
                # Store the token in the session
                token_data = response.json()
                access_token = token_data.get('access_token')
                
                if not access_token:
                    logger.error("No access token in response")
                    messages.error(request, "Authentication failed: No access token received")
                    return render(request, 'core/login.html')
                
                request.session['token'] = access_token
                logger.info("Successfully obtained access token")
                
                # Create a local user for Django's authentication
                from django.contrib.auth.models import User
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'email': f"{username}@example.com"}
                )
                if created:
                    user.set_password(password)
                    user.save()
                    logger.info(f"Created new local user for {username}")
                
                login(request, user)
                messages.success(request, 'Successfully logged in!')
                return redirect('dashboard')
            else:
                error_detail = response.json().get('detail', 'Invalid credentials')
                messages.error(request, f"Login failed: {error_detail}")
                logger.error(f"Login failed for user {username}. Status: {response.status_code}, Response: {response.text}")
        except requests.RequestException as e:
            messages.error(request, f"Unable to connect to authentication service: {str(e)}")
            logger.error(f"Authentication service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            messages.error(request, "An unexpected error occurred")
    
    return render(request, 'core/login.html')

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
