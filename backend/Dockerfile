# Production Dockerfile for Django Backend
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies with legacy resolver
RUN pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt

# Copy project files
COPY . .

# Copy Google File 
COPY gen-lang-client-0598591486-ee1fab7d978e.json /app/

# Create necessary directories
RUN mkdir -p /app/data /app/staticfiles /app/media

# Note: collectstatic will be run during deployment after migrations
# RUN python manage.py collectstatic --noinput || true

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=5)"


# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "menumine_ai.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]

