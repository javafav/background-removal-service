# Use a small, recent python image
FROM python:3.11-slim

WORKDIR /app

# avoid interactive prompts and reduce image size
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
 && rm -rf /var/lib/apt/lists/*

# Install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run with gunicorn (change workers if you need more)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers", "1"]
