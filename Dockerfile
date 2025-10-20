# Use Python 3.14 slim image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libtiff5-dev \
    libopenjp2-7-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml poetry.lock README.md ./
COPY src/ ./src/
COPY app.py start_server.py ./

# Install Python dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV MCP_DATA_DIR=/app/data
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8032
ENV MCP_PATH=/mcp/
ENV MCP_WORKERS=1

# Expose port
EXPOSE 8032

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8032/health || exit 1

# Run the application
CMD ["python", "start_server.py"]
