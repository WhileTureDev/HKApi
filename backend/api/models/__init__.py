# models/__init__.py

from utils.database import Base, metadata  # Use absolute import
from .userModel import User
from .projectModel import Project
from .namespaceModel import Namespace
from .deploymentModel import Deployment
from .userProjectModel import UserProject
from .adminModel import Admin  # Ensure this is imported as well
