FROM python:3.10-slim-buster

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Helm
RUN apt-get update && apt-get install -y curl gnupg dos2unix
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && \
    chmod 700 get_helm.sh && \
    ./get_helm.sh && \
    rm -f get_helm.sh
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN   mv kubectl  /usr/local/bin/
RUN   chmod +x /usr/local/bin/kubectl

# Install application dependencies

WORKDIR /code
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install psycopg2-binary


COPY ./app /code/app


EXPOSE 8000

# Run the application
COPY ./entrypoint.sh .
RUN  chmod +x ./entrypoint.sh && \
     dos2unix ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
