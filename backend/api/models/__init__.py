from .userModel import User
from .projectModel import Project
from .namespaceModel import Namespace
from .deploymentModel import Deployment
from .userProjectModel import UserProject
from .adminModel import Admin

from ..utils.database import Base, engine

# This ensures all models are imported and metadata is created
Base.metadata.create_all(bind=engine)
