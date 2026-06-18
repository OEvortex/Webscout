# =============================================================================
# Multi-stage Dockerfile for LLM4Free API Server
# Optimized for production with security, performance, and size considerations
# No external docker/ directory required - works with pip/git installations
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and build the application
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Set build arguments for flexibility
ARG LLM4FREE_VERSION=latest
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set environment variables for build optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for better dependency isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Install llm4free with API dependencies
# Use specific version if provided, otherwise latest
RUN if [ "$LLM4FREE_VERSION" = "latest" ]; then \
        pip install git+https://github.com/OEvortex/LLM4Free.git#egg=llm4free[api]; \
    else \
        pip install git+https://github.com/OEvortex/LLM4Free.git@${LLM4FREE_VERSION}#egg=llm4free[api]; \
    fi

# Install additional production dependencies
RUN pip install \
    gunicorn[gthread] \
    uvicorn[standard] \
    prometheus-client \
    structlog

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Create minimal production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

# Set runtime arguments and labels for metadata
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL maintainer="OEvortex" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="llm4free-api" \
      org.label-schema.description="LLM4Free API Server - OpenAI-compatible LLM proxy" \
      org.label-schema.url="https://github.com/OEvortex/LLM4Free" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/OEvortex/LLM4Free" \
      org.label-schema.vendor="OEvortex" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Create non-root user for security
RUN groupadd --gid 1000 llm4free && \
    useradd --uid 1000 --gid llm4free --shell /bin/bash --create-home llm4free

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    # Security settings
    PYTHONHASHSEED=random \
    # Performance settings
    MALLOC_ARENA_MAX=2 \
    # Application settings
    LLM4FREE_HOST=0.0.0.0 \
    LLM4FREE_PORT=8000 \
    LLM4FREE_WORKERS=1 \
    LLM4FREE_LOG_LEVEL=info \
    LLM4FREE_DEBUG=false \
    LLM4FREE_DATA_DIR=/app/data \
    LLM4FREE_REQUEST_LOGGING=true \
    # FastAPI metadata
    LLM4FREE_API_TITLE="LLM4Free OpenAI API" \
    LLM4FREE_API_DESCRIPTION="OpenAI API compatible interface for various LLM providers" \
    LLM4FREE_API_VERSION="0.2.0" \
    LLM4FREE_API_DOCS_URL="/docs" \
    LLM4FREE_API_REDOC_URL="/redoc" \
    LLM4FREE_API_OPENAPI_URL="/openapi.json" \
    # Dynamic configuration defaults
    LLM4FREE_CORS_ORIGINS="*"

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for some Python packages
    libffi8 \
    libssl3 \
    # Useful for debugging (can be removed for minimal image)
    curl \
    # Health check utilities
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application directory and set ownership
WORKDIR /app
RUN chown -R llm4free:llm4free /app

# Copy application files (if building from source)
# COPY --chown=llm4free:llm4free . /app

# Create directories for logs and data with proper permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R llm4free:llm4free /app/logs /app/data

# Switch to non-root user
USER llm4free

# Expose port (configurable via environment)
EXPOSE $LLM4FREE_PORT

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${LLM4FREE_PORT:-8000}/monitor/health || exit 1

# Default command - start the llm4free API server with new auth system
# Environment variables will be used by the application
CMD ["python", "-m", "llm4free.server.server"]
