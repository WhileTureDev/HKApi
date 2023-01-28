FROM python:3.10-slim-buster

# Install Helm
RUN apt-get update && apt-get install -y curl gnupg
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && \
    chmod 700 get_helm.sh && \
    ./get_helm.sh && \
    rm -f get_helm.sh

# Install application dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
WORKDIR /app
# Copy application code
COPY src .

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]