FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgmp3-dev \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional crypto libraries for better performance
RUN pip install --no-cache-dir coincurve

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command
CMD ["python3", "plutus.py"]