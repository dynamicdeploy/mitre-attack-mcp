# MITRE ATT&CK MCP Server Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8032
ENV MCP_TRANSPORT=http

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and poetry.lock for dependency management
COPY pyproject.toml poetry.lock ./

# Install Poetry and dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main --no-root

# Copy source code
COPY src/ ./src/
COPY examples/ ./examples/

# Create data directory
RUN mkdir -p /app/data

# Set data directory environment variable
ENV MCP_DATA_DIR=/app/data

# Expose port
EXPOSE 8032

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8032/ || exit 1

# Run the server
CMD ["python", "src/mitre_attack_mcp/server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8032"]