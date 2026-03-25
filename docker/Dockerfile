# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (iptables, etc.)
RUN apt-get update && apt-get install -y \
    iptables \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose API port
EXPOSE 8000

# Default command (will be overridden in docker-compose for workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
