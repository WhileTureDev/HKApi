from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class TokenAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip authentication for public paths
        public_paths = ['/login/', '/signup/', '/', '/static/', '/favicon.ico']
        if any(request.path.startswith(path) for path in public_paths):
            return self.get_response(request)

        # Skip authentication for static files
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        # Check if user is authenticated
        if not request.user.is_authenticated:
            token = request.session.get('token')
            username = request.session.get('username')

            if token and username:
                # Create or get a Django user for session management
                user, created = User.objects.get_or_create(username=username)
                if created:
                    user.save()
                login(request, user)
                logger.info(f"User {username} authenticated via token")
            else:
                if token and not username:
                    logger.warning("Token present but no username in session")
                    request.session.flush()
                    return redirect('login')
                else:
                    logger.debug("No authentication credentials found")
                    return redirect('login')

        response = self.get_response(request)
        return response
