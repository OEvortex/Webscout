# Deployment Guide

> **Last updated:** 2026-01-24  
> **Type:** Operations Guide  
> **Audience:** DevOps, system administrators

## Overview

LLM4Free can be deployed in multiple ways:

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
docker pull oevortex/llm4free:latest

# Specific version
docker pull oevortex/llm4free:2024.12.01

# Latest slim version (smaller)
docker pull oevortex/llm4free:slim
```

### Run Container

```bash
# Interactive mode
docker run -it oevortex/llm4free:latest

# With API key mounted
docker run -it \
  -e OPENAI_API_KEY="your-api-key" \
  oevortex/llm4free:latest

# With port forwarding (for API server)
docker run -it \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key" \
  oevortex/llm4free:latest \
  llm4free-server
```

### Build Custom Image

```dockerfile
FROM oevortex/llm4free:latest

# Add custom requirements
RUN pip install additional-package

# Set default command
CMD ["llm4free", "--help"]
```

```bash
# Build
docker build -t my-llm4free .

# Run
docker run -it my-llm4free
```

---

## Docker Compose

### Basic Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  llm4free:
    image: oevortex/llm4free:latest
    container_name: llm4free-app
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./data:/app/data
    ports:
      - "8000:8000"
    stdin_open: true
    tty: true

  llm4free-server:
    image: oevortex/llm4free:latest
    container_name: llm4free-api
    command: llm4free-server --host 0.0.0.0 --port 8001
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
    ports:
      - "8001:8001"
    depends_on:
      - llm4free
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
docker-compose logs -f llm4free-server

# Stop services
docker-compose down
```

### With Authentication (Optional)

```yaml
services:
  llm4free-server:
    image: oevortex/llm4free:latest
    command: >
      llm4free-server
      --host 0.0.0.0
      --port 8001
      --api-key gsk_llm4free_prod_12345
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8001:8001"
```

---

## OpenAI-Compatible API Server

### What It Does

Runs a FastAPI server that proxies any LLM4Free provider through OpenAI-compatible endpoints.

```
Your App → llm4free-server (OpenAI API) → Any LLM4Free Provider
```

### Start Server

```bash
# Simple start
llm4free-server

# With custom host/port
llm4free-server --host 0.0.0.0 --port 8001

# With debug mode
llm4free-server --debug

# With API key requirement
llm4free-server --api-key your-secret-key
```

### Configure Providers

Create `llm4free_config.json`:

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

# Point to your LLM4Free server
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
LLM4FREE_HOST=0.0.0.0
LLM4FREE_PORT=8000
LLM4FREE_DEBUG=false

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

Create `llm4free.yaml`:

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
limit_req_zone $binary_remote_addr zone=llm4free:10m rate=10r/s;

server {
    location / {
        limit_req zone=llm4free burst=20 nodelay;
        proxy_pass http://llm4free:8000;
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
  llm4free-1:
    image: oevortex/llm4free:latest
    ports:
      - "8001:8000"
  
  llm4free-2:
    image: oevortex/llm4free:latest
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
  name: llm4free-deployment

spec:
  replicas: 3
  
  selector:
    matchLabels:
      app: llm4free
  
  template:
    metadata:
      labels:
        app: llm4free
    
    spec:
      containers:
      - name: llm4free
        image: oevortex/llm4free:latest
        ports:
        - containerPort: 8000
        
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm4free-secrets
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
docker ps | grep llm4free

# Check logs
docker logs llm4free-api

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
docker exec llm4free-api env | grep -i api

# Set in docker-compose
environment:
  - GROQ_API_KEY=${GROQ_API_KEY}
```

### High memory usage

```bash
# Monitor container memory
docker stats llm4free-api

# Limit memory in docker-compose
services:
  llm4free:
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
