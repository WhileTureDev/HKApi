# Monitoring and Metrics Implementation

In the recent updates, we have implemented monitoring and metrics functionality for the FastAPI application to enhance observability and provide insights into the application's performance and health. Below are the details of the implemented features:

1. Metrics Collection with Prometheus

We have integrated Prometheus to collect and expose metrics related to API requests and system performance. The metrics include:
- Request Count (REQUEST_COUNT): Tracks the total number of requests received by the application.
- Request Latency (REQUEST_LATENCY): Measures the time taken to process each request.
- In-Progress Requests (IN_PROGRESS): Counts the number of requests currently being processed.
- Error Count (ERROR_COUNT): Records the number of requests that resulted in an error.

2. Health Check Endpoint

A health check endpoint has been implemented to allow for the regular monitoring of the application's health status. This endpoint performs a basic database connectivity check and responds with the application's status.

Endpoint: /api/v1/health
- Method: GET
- Response:
  - 200 OK if the application is healthy
  - 500 Internal Server Error if there is an issue with the database connection

```python
@router.get("/api/v1/health", response_model=dict)
async def health_check(db: Session = Depends(get_db)):
    start_time = time.time()
    endpoint = "/api/v1/health"
    method = "GET"
    IN_PROGRESS.labels(endpoint=endpoint).inc()

    try:
        call_database_operation(lambda: db.execute(text("SELECT 1")))
        logger.info("Health check passed")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
        raise HTTPException(status_code=500, detail="Health check failed")
    finally:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        IN_PROGRESS.labels(endpoint=endpoint).dec()

```

3. Integration of Metrics in Controllers

All existing controllers have been updated to include the collection of metrics. This involves tracking the number of requests, latency, in-progress requests, and errors for each endpoint. The metrics are collected using the Prometheus client and are exposed at the /metrics endpoint for Prometheus to scrape.

Example Update in Controllers:

```python
from controllers.monitorControllers.metricsController import (
  REQUEST_COUNT, REQUEST_LATENCY, IN_PROGRESS, ERROR_COUNT
)


@router.post("/projects/", response_model=ProjectSchema)
def create_project(
        request: Request,
        project: ProjectCreate,
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
):
  start_time = time.time()
  method = "POST"
  endpoint = "/projects/"
  IN_PROGRESS.labels(endpoint=endpoint).inc()

  try:
    logger.info(f"User {current_user.username} is creating a new project: {project.name}")

    existing_project = call_database_operation(
      lambda: db.query(ProjectModel).filter(ProjectModel.name == project.name).first())
    if existing_project:
      logger.warning(f"Project with name {project.name} already exists")
      raise HTTPException(status_code=400, detail="Project with this name already exists")

    new_project = ProjectModel(
      name=project.name,
      description=project.description,
      owner_id=current_user.id,
      created_at=datetime.utcnow(),
      updated_at=datetime.utcnow()
    )
    call_database_operation(lambda: db.add(new_project))
    call_database_operation(lambda: db.commit())
    call_database_operation(lambda: db.refresh(new_project))
    logger.info(f"Project {project.name} created successfully")
    return new_project
  except HTTPException as http_exc:
    ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
    raise http_exc
  except Exception as e:
    logger.error(f"An error occurred while creating project: {str(e)}")
    ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()
    raise HTTPException(status_code=500, detail="An internal error occurred")
  finally:
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
    IN_PROGRESS.labels(endpoint=endpoint).dec()

```

## Summary
These updates ensure that the FastAPI application is now equipped with essential monitoring capabilities, allowing administrators to track the performance and health of the application in real-time. The metrics collected provide valuable insights that can be used for debugging, performance tuning, and ensuring the overall reliability of the system.