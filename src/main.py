from fastapi import FastAPI
from namespace import create_namespace
from db import create_namespace_record
import subprocess
from kubernetes import config

app = FastAPI()


@app.post("/deploy")
def deploy(chart_name: str, chart_repo: str):
    # Authenticate against kubernetes cluster
    try:
        config.load_incluster_config()
    except Exception as e:
        return e
    # Create namespace
    try:
        namespace = create_namespace()
    except Exception as e:
        return e
    if create_namespace():
        create_namespace_record(chart_name, chart_repo, namespace)
        # Deploy the chart
        try:
            subprocess.run(["helm", "repo", "add", chart_repo, chart_repo])
            subprocess.run(
                ["helm", "upgrade", chart_name, chart_repo + "/" + chart_name, "--install", "--namespace", namespace])
        except Exception as e:
            print(e)
        return {"status": f"deployment {chart_name} successful"}
    else:
        return {"status": "failed"}


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
