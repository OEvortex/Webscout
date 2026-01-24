# Deployment Guide

> **Last updated:** 2026-01-24  
> **Type:** Operations Guide  
> **Audience:** DevOps, system administrators

## Overview

Webscout can be deployed in multiple ways:

- **Docker** — Containerized deployment (recommended)
- **Docker Compose** — Multi-service orchestration
- **OpenAI-Compatible API Server** — Local HTTP API
- **Bare Metal** — Direct Python installation

---

## Table of Contents

1. [Docker Setup](#docker-setup)
2. [Docker Compose](#docker-compose)
3. [OpenAI-Compatible API Server](#openai-compatible-api-server)
4. [Environment Configuration](#environment-configuration)
5. [Production Considerations](#production-considerations)
6. [Troubleshooting](#troubleshooting)

---

## Docker Setup

### Pull Official Image

```bash
# Latest version
docker pull oevortex/webscout:latest

# Specific version
docker pull oevortex/webscout:2024.12.01

# Latest slim version (smaller)
docker pull oevortex/webscout:slim
```

### Run Container

```bash
# Interactive mode
docker run -it oevortex/webscout:latest

# With API key mounted
docker run -it \
  -e OPENAI_API_KEY="your-api-key" \
  oevortex/webscout:latest

# With port forwarding (for API server)
docker run -it \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key" \
  oevortex/webscout:latest \
  webscout-server
```

### Build Custom Image

```dockerfile
FROM oevortex/webscout:latest

# Add custom requirements
RUN pip install additional-package

# Set default command
CMD ["webscout", "--help"]
```

```bash
# Build
docker build -t my-webscout .

# Run
docker run -it my-webscout
```

---

## Docker Compose

### Basic Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  webscout:
    image: oevortex/webscout:latest
    container_name: webscout-app
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./data:/app/data
    ports:
      - "8000:8000"
    stdin_open: true
    tty: true

  webscout-server:
    image: oevortex/webscout:latest
    container_name: webscout-api
    command: webscout-server --host 0.0.0.0 --port 8001
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
    ports:
      - "8001:8001"
    depends_on:
      - webscout
```

### Run Compose Stack

```bash
# Create .env file with your API keys
cat > .env << EOF
OPENAI_API_KEY=your-api-key-here
GROQ_API_KEY=your-groq-key-here
EOF

# Start services
docker-compose up -d

# View logs
docker-compose logs -f webscout-server

# Stop services
docker-compose down
```

### With Authentication (Optional)

```yaml
services:
  webscout-server:
    image: oevortex/webscout:latest
    command: >
      webscout-server
      --host 0.0.0.0
      --port 8001
      --api-key gsk_webscout_prod_12345
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8001:8001"
```

---

## OpenAI-Compatible API Server

### What It Does

Runs a FastAPI server that proxies any Webscout provider through OpenAI-compatible endpoints.

```
Your App → webscout-server (OpenAI API) → Any Webscout Provider
```

### Start Server

```bash
# Simple start
webscout-server

# With custom host/port
webscout-server --host 0.0.0.0 --port 8001

# With debug mode
webscout-server --debug

# With API key requirement
webscout-server --api-key your-secret-key
```

### Configure Providers

Create `webscout_config.json`:

```json
{
  "default_provider": "GROQ",
  "providers": {
    "GROQ": {
      "api_key": "${GROQ_API_KEY}",
      "model": "llama-3.1-70b-versatile"
    },
    "OpenAI": {
      "api_key": "${OPENAI_API_KEY}",
      "model": "gpt-4"
    }
  }
}
```

### Use with OpenAI Client

```python
from openai import OpenAI

# Point to your Webscout server
client = OpenAI(
    api_key="any-key-or-gsk_...",
    base_url="http://localhost:8000/v1"
)

# Use exactly like OpenAI
response = client.chat.completions.create(
    model="GROQ",
    messages=[
        {"role": "user", "content": "Hello"}
    ]
)

print(response.choices[0].message.content)
```

### API Endpoints

#### Chat Completions

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR-API-KEY" \
  -d '{
    "model": "GROQ",
    "messages": [
      {"role": "user", "content": "Hello"}
    ]
  }'
```

#### List Models

```bash
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer YOUR-API-KEY"
```

#### Health Check

```bash
curl http://localhost:8000/health
```

---

## Environment Configuration

### API Keys

Set environment variables:

```bash
# Linux/macOS
export OPENAI_API_KEY="sk-..."
export GROQ_API_KEY="gsk_..."
export COHERE_API_KEY="..."

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."
$env:GROQ_API_KEY = "gsk_..."

# Windows CMD
set OPENAI_API_KEY=sk-...
```

### Using .env File

Create `.env`:

```bash
# AI Provider Keys
OPENAI_API_KEY=sk-your-openai-key
GROQ_API_KEY=gsk_your-groq-key
COHERE_API_KEY=co_your-cohere-key
GEMINI_API_KEY=your-gemini-key

# Server Configuration
WEBSCOUT_HOST=0.0.0.0
WEBSCOUT_PORT=8000
WEBSCOUT_DEBUG=false

# Timeout settings
REQUEST_TIMEOUT=30
STREAM_TIMEOUT=120
```

Load with:

```bash
# Shell
set -a
source .env
set +a

# Or in Python
from dotenv import load_dotenv
load_dotenv()
```

### Configuration File

Create `webscout.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8000
  debug: false
  workers: 4
  timeout: 30

providers:
  GROQ:
    api_key: ${GROQ_API_KEY}
    model: llama-3.1-70b-versatile
    timeout: 60
  
  OpenAI:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
    timeout: 30

logging:
  level: INFO
  format: json
```

---

## Production Considerations

### 1. Security

#### Use HTTPS

```bash
# With self-signed certificate
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem -out cert.pem -days 365 -nodes

# Use with nginx reverse proxy
nginx
```

#### Environment Variables

```bash
# Never commit secrets
echo ".env" >> .gitignore

# Use secure secret management
# - Kubernetes Secrets
# - AWS Secrets Manager
# - HashiCorp Vault
# - Docker Secrets
```

#### Rate Limiting

```yaml
# In nginx config
limit_req_zone $binary_remote_addr zone=webscout:10m rate=10r/s;

server {
    location / {
        limit_req zone=webscout burst=20 nodelay;
        proxy_pass http://webscout:8000;
    }
}
```

### 2. Monitoring

#### Health Checks

```bash
# Docker
docker run --healthcheck=CMD curl -f http://localhost:8000/health

# Kubernetes
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
```

#### Logging

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### Metrics

```bash
# Prometheus metrics endpoint
curl http://localhost:8000/metrics
```

### 3. Performance

#### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_provider_instance(provider_name: str):
    return initialize_provider(provider_name)
```

#### Connection Pooling

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
```

#### Load Balancing

```yaml
# docker-compose with multiple instances
services:
  webscout-1:
    image: oevortex/webscout:latest
    ports:
      - "8001:8000"
  
  webscout-2:
    image: oevortex/webscout:latest
    ports:
      - "8002:8000"
  
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### 4. Scaling

#### Horizontal Scaling (Kubernetes)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webscout-deployment

spec:
  replicas: 3
  
  selector:
    matchLabels:
      app: webscout
  
  template:
    metadata:
      labels:
        app: webscout
    
    spec:
      containers:
      - name: webscout
        image: oevortex/webscout:latest
        ports:
        - containerPort: 8000
        
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: webscout-secrets
              key: groq-api-key
        
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

## Troubleshooting

### "Connection refused" when accessing API

```bash
# Check if server is running
docker ps | grep webscout

# Check logs
docker logs webscout-api

# Verify port is open
netstat -tulpn | grep 8000

# Test locally
curl http://localhost:8000/health
```

### "API key not found" errors

```bash
# Verify environment variables are set
echo $GROQ_API_KEY
echo $OPENAI_API_KEY

# Check in Docker
docker exec webscout-api env | grep -i api

# Set in docker-compose
environment:
  - GROQ_API_KEY=${GROQ_API_KEY}
```

### High memory usage

```bash
# Monitor container memory
docker stats webscout-api

# Limit memory in docker-compose
services:
  webscout:
    mem_limit: 1g
```

### SSL/TLS certificate errors

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/private.key \
  -out /etc/nginx/ssl/certificate.crt

# Use with proper nginx config
```

---

## Deployment Checklist

- [ ] API keys configured securely
- [ ] HTTPS/SSL enabled
- [ ] Health checks working
- [ ] Logging configured
- [ ] Monitoring in place
- [ ] Backups configured
- [ ] Rate limiting enabled
- [ ] Firewall rules set
- [ ] Documentation updated
- [ ] Test deployment first

---

## See Also

- [Getting Started](getting-started.md)
- [API Reference](api-reference.md)
- [Docker Documentation](DOCKER.md)
- [OpenAI API Server](openai-api-server.md)
