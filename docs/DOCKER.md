# Docker Setup for LLM4Free

This Docker configuration is designed to work seamlessly when LLM4Free is installed via pip or git+pip, without requiring any external docker directory or entrypoint scripts. It supports the new enhanced authentication system with no-auth mode for flexible deployment scenarios.

## Quick Start

### Build and Run

```bash
# Build the image
docker build -t llm4free-api .

# Run the container (default port 8000, with authentication)
docker run -p 8000:8000 llm4free-api

# Run with no authentication required (great for development/demos)
docker run -p 8000:8000 -e LLM4FREE_NO_AUTH=true llm4free-api

# Run with no authentication and no rate limiting (maximum openness)
docker run -p 8000:8000 -e LLM4FREE_NO_AUTH=true -e LLM4FREE_NO_RATE_LIMIT=true llm4free-api

# Run with custom port (e.g., 7860)
docker run -p 7860:7860 -e LLM4FREE_PORT=7860 llm4free-api

# Run with MongoDB support
docker run -p 8000:8000 -e MONGODB_URL=mongodb://localhost:27017 llm4free-api
```

### Using Docker Compose

```bash
# Basic setup (with authentication)
docker-compose up llm4free-api

# No-auth mode for development/demos
docker-compose -f docker-compose.yml -f docker-compose.no-auth.yml up llm4free-api

# With custom port
LLM4FREE_PORT=7860 docker-compose up llm4free-api

# Production setup with Gunicorn
docker-compose --profile production up llm4free-api-production

# Development setup with hot reload
docker-compose --profile development up llm4free-api-dev

# MongoDB setup with authentication
docker-compose --profile mongodb up
```

### Using Makefile

```bash
# Quick start (build + run + test)
make quick-start

# Build image
make build

# Start services
make up

# View logs
make logs

# Run health check
make health

# Clean up
make clean
```

## Configuration

### Environment Variables

The LLM4Free server reads the following environment variables at runtime. The server configuration is dynamically determined from code defaults unless explicitly overridden via environment variables.

#### **Core Server Settings**
- `LLM4FREE_HOST` - Server host (default: 0.0.0.0 from ServerConfig)
- `LLM4FREE_PORT` - Server port (default: 8000 from ServerConfig)
- `LLM4FREE_WORKERS` - Number of worker processes (default: 1)
- `LLM4FREE_LOG_LEVEL` - Log level: debug, info, warning, error, critical (default: info)
- `LLM4FREE_DEBUG` - Enable debug mode (default: false from ServerConfig)
- `LLM4FREE_API_TITLE` - FastAPI app title (default: "LLM4Free API" from code)
- `LLM4FREE_API_DESCRIPTION` - FastAPI app description (default: "OpenAI API compatible interface for various LLM providers" from code)
- `LLM4FREE_API_VERSION` - FastAPI app version (default: "0.2.0" from code)
- `LLM4FREE_API_DOCS_URL` - FastAPI docs URL (default: /docs from code)
- `LLM4FREE_API_REDOC_URL` - FastAPI redoc URL (default: /redoc from code)
- `LLM4FREE_API_OPENAPI_URL` - FastAPI OpenAPI URL (default: /openapi.json from code)

#### **Authentication & Security** 🔐
- `LLM4FREE_REQUEST_LOGGING` - Enable request logging (default: true from ServerConfig)
- `LLM4FREE_API_KEY` - Legacy API key for authentication (optional)

**Dynamic Configuration**: The server also supports configuring the following programmatically through ServerConfig class:
- `auth_required` - Authentication required flag (default: false from ServerConfig)
- `rate_limit_enabled` - Rate limiting enabled flag (default: false from ServerConfig)
- `cors_origins` - CORS allowed origins (default: ["*"] from ServerConfig)
- `max_request_size` - Maximum request size (default: 10MB from ServerConfig)
- `request_timeout` - Request timeout in seconds (default: 300 from ServerConfig)

#### **Database Configuration** 🗄️
- `LLM4FREE_DATA_DIR` - Data directory for JSON database (default: /app/data from ServerConfig)

#### **Provider Settings**
- `LLM4FREE_DEFAULT_PROVIDER` - Default LLM provider (default: ChatGPT from ServerConfig)
- `LLM4FREE_BASE_URL` - Base URL for the API (default: None from ServerConfig)

**Legacy Support**: For backward compatibility, the following legacy environment variables are also supported:
- `PORT` (fallback for `LLM4FREE_PORT`)
- `API_KEY` (fallback for `LLM4FREE_API_KEY`)
- `DEFAULT_PROVIDER` (fallback for `LLM4FREE_DEFAULT_PROVIDER`)
- `BASE_URL` (fallback for `LLM4FREE_BASE_URL`)
- `DEBUG` (fallback for `LLM4FREE_DEBUG`)

**Note**: When both LLM4FREE_* and legacy variables are set, LLM4FREE_* takes precedence.

### Service Profiles

- **Default**: Basic API server with enhanced authentication system
- **No-Auth**: Development/demo mode with no authentication required 🔓
- **Production**: Gunicorn with multiple workers and optimized settings
- **Development**: Uvicorn with hot reload and debug logging
- **MongoDB**: Full setup with MongoDB database support 🗄️
- **Nginx**: Optional reverse proxy (requires custom nginx.conf)
- **Monitoring**: Optional Prometheus monitoring (requires custom prometheus.yml)

## Features

- ✅ No external docker directory required
- ✅ Works with pip/git installations
- ✅ Multi-stage build for optimized image size
- ✅ Non-root user for security
- ✅ Health checks included
- ✅ Multiple deployment profiles
- ✅ **NEW!** No-auth mode for development/demos 🔓
- ✅ **NEW!** Enhanced authentication system with API key management 🔑
- ✅ **NEW!** MongoDB and JSON database support 🗄️
- ✅ **NEW!** Rate limiting with IP-based fallback 🛡️
- ✅ Comprehensive Makefile for easy management
- ✅ Volume mounts for logs and data persistence

## Health Checks

The setup includes automatic health checks that verify the `/health` endpoint is responding correctly. This endpoint provides comprehensive system status including database connectivity and authentication system status.

## Security

- Runs as non-root user (`llm4free:llm4free`)
- Minimal runtime dependencies
- Security-optimized container settings
- **Enhanced authentication system** with API key management 🔑
- **Rate limiting** to prevent abuse 🛡️
- **No-auth mode** for development (use with caution in production) 🔓
- **Database encryption** support with MongoDB
- **Secure API key generation** with cryptographic randomness

## Troubleshooting

### Check container status
```bash
make status
```

### View logs
```bash
make logs
```

### Test endpoints
```bash
make test-endpoints
```

### Access container shell
```bash
make shell
```
