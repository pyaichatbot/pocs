# Deployment Guide

## Overview

This guide covers deploying ADK agents to various platforms and environments.

## Local Deployment

### Running Locally

```python
# agent.py
from google.adk import LLMAgent

agent = LLMAgent(...)

if __name__ == "__main__":
    response = agent.run("Hello")
    print(response)
```

```bash
python agent.py
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY agent.py .
COPY config.yaml .

# Expose port
EXPOSE 8080

# Run agent
CMD ["python", "agent.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
    volumes:
      - ./credentials.json:/app/credentials.json
```

## Agent Engine Deployment

### Setup

Agent Engine is Google Cloud's managed service for ADK agents.

```bash
# Install Agent Engine CLI
gcloud components install agent-engine

# Initialize agent
gcloud agent-engine agents create my-agent \
    --agent-file=agent.py \
    --region=us-central1
```

### Configuration

```yaml
# agent-config.yaml
agent:
  name: my-agent
  model:
    name: gemini-2.0-flash-exp
  resources:
    cpu: 1
    memory: 2Gi
  scaling:
    min_instances: 1
    max_instances: 10
```

### Deploy

```bash
gcloud agent-engine agents deploy my-agent \
    --config=agent-config.yaml
```

## Cloud Run Deployment

### Cloud Run Setup

```python
# main.py
from flask import Flask, request, jsonify
from google.adk import LLMAgent

app = Flask(__name__)
agent = LLMAgent(...)

@app.route("/", methods=["POST"])
def handle_request():
    data = request.json
    query = data.get("query", "")
    response = agent.run(query)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
```

### Deploy to Cloud Run

```bash
# Build and deploy
gcloud run deploy my-agent \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

### Cloud Run with A2A

```python
# main.py
from a2a_sdk import AgentServer
from google.adk import LLMAgent

agent = LLMAgent(...)
server = AgentServer(agent)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)
```

## GKE Deployment

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent
  template:
    metadata:
      labels:
        app: agent
    spec:
      containers:
      - name: agent
        image: gcr.io/my-project/agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: /app/credentials.json
---
apiVersion: v1
kind: Service
metadata:
  name: agent-service
spec:
  selector:
    app: agent
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

### Deploy to GKE

```bash
# Build image
gcloud builds submit --tag gcr.io/my-project/agent

# Deploy
kubectl apply -f deployment.yaml
```

## Environment Configuration

### Environment Variables

```python
import os
from google.adk import LLMAgent
from google.adk.models import GeminiModel

model = GeminiModel(
    model_name=os.getenv("MODEL_NAME", "gemini-2.0-flash-exp"),
    temperature=float(os.getenv("TEMPERATURE", "0.7"))
)

agent = LLMAgent(model=model)
```

### Configuration Files

```yaml
# config.yaml
agent:
  model:
    name: ${MODEL_NAME}
    temperature: ${TEMPERATURE}
  tools:
    - weather_tool
    - search_tool
```

```python
from google.adk.config import load_config
import os

config = load_config("config.yaml", env_vars=os.environ)
agent = LLMAgent.from_config(config)
```

## Security

### Service Account

```bash
# Create service account
gcloud iam service-accounts create agent-sa

# Grant permissions
gcloud projects add-iam-policy-binding my-project \
    --member="serviceAccount:agent-sa@my-project.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Use in deployment
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
```

### Secrets Management

```python
from google.cloud import secretmanager

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

## Monitoring

### Logging

```python
import logging
from google.cloud import logging as cloud_logging

cloud_logging.Client().setup_logging()

logging.info("Agent started")
```

### Metrics

```python
from google.cloud import monitoring_v3

client = monitoring_v3.MetricServiceClient()
# Send custom metrics
```

### Health Checks

```python
from flask import Flask

app = Flask(__name__)

@app.route("/health")
def health():
    return {"status": "healthy"}, 200
```

## Scaling

### Auto-scaling

```yaml
# Cloud Run
autoscaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.8
```

### Load Balancing

```yaml
# GKE
apiVersion: v1
kind: Service
spec:
  type: LoadBalancer
  sessionAffinity: ClientIP
```

## Best Practices

1. **Resource Limits**: Set appropriate CPU/memory limits
2. **Health Checks**: Implement health check endpoints
3. **Logging**: Enable comprehensive logging
4. **Monitoring**: Set up metrics and alerts
5. **Security**: Use service accounts and secrets
6. **Scaling**: Configure auto-scaling appropriately
7. **Testing**: Test deployment process thoroughly

## References

- Agent Engine: https://cloud.google.com/agent-engine
- Cloud Run: https://cloud.google.com/run
- GKE: https://cloud.google.com/kubernetes-engine

