FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optimized for smaller size)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose port
EXPOSE 5000

# Set environment variables for production
ENV PYTHONUNBUFFERED=1

# Run with gunicorn optimized for free tier
# - 1 worker to reduce memory usage
# - 120s timeout for background removal processing
# - Lower worker connections
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "1", "--threads", "2", "--worker-class", "gthread", "app:app"]