import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from controllers.helmControllers import helmRepositoryController, helmController
from controllers.k8sControllers import podController, deploymentController, namespaceController
from controllers.monitorControllers import metricsController
from utils.helm import load_k8s_config, configure_helm_repositories
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(helmRepositoryController.router, prefix="/api/v1", tags=["Helm Repository"])
app.include_router(helmController.router, prefix="/api/v1", tags=["Helm"])
app.include_router(podController.router, prefix="/api/v1", tags=["Pod"])
app.include_router(deploymentController.router, prefix="/api/v1", tags=["Deployment"])
app.include_router(namespaceController.router, prefix="/api/v1", tags=["Namespace"])
app.include_router(metricsController.router, prefix="/api/v1", tags=["Monitoring"])

@app.on_event("startup")
async def startup_event():
    # Load Kubernetes configuration
    load_k8s_config()
    # Configure Helm repositories from in-memory storage
    configure_helm_repositories()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
def read_root():
    return {"message": "Welcome to HKApi"}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for the API."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
