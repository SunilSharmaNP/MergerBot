# Stage 1: Build stage with build dependencies
FROM python:3.9-slim-bullseye AS builder

# Set working directory
WORKDIR /usr/src/app

# Install system dependencies needed for building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python build dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip wheel --no-cache-dir --wheel-dir=/usr/src/app/wheels -r requirements.txt


# Stage 2: Final production stage
FROM python:3.9-slim-bullseye

# Set working directory
WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage and install
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache-dir /wheels/*

# Copy application code into the container
COPY . .

# Create downloads directory and set permissions
RUN mkdir -p downloads logs && \
    chown -R www-data:www-data downloads logs

# Switch to a non-root user for security
USER www-data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port (useful for health checks if you add a web server)
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]
