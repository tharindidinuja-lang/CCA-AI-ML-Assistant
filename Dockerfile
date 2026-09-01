# syntax=docker/dockerfile:1
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements file first
COPY requirements.txt .

# Install python packages with cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --default-timeout=500 --retries=10 -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Command to run the FastAPI server via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]