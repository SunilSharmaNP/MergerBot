# --- Stage 1: Builder ---
# This stage builds the Python dependencies
FROM python:3.9-slim-bullseye AS builder

# Set working directory
WORKDIR /usr/src/app

# Install build essentials for some python packages
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir=/usr/src/app/wheels -r requirements.txt

# --- Stage 2: Final Production Image ---
# This is the final, lean image that will run the bot
FROM python:3.9-slim-bullseye

# Set the timezone to UTC to fix the Telegram time sync error
ENV TZ=UTC

# Set working directory for the app
WORKDIR /app

# Install system dependencies (ffmpeg for video processing, tzdata for time)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg tzdata && \
    # Configure the timezone
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    # Clean up apt cache
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from the builder stage
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir /wheels/*

# Copy the application code into the container
COPY . .

# Create a non-root user for security
RUN useradd -m -s /bin/bash www-data

# Create necessary directories and set correct permissions
# The app will write session files and downloads here
RUN mkdir -p downloads && \
    chown -R www-data:www-data /app downloads

# Switch to the non-root user
USER www-data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Command to run the bot
CMD ["python", "-m", "main"]
