# Use official Python slim image as base
FROM python:3.11-slim

# Set environment variables to prevent Python buffering & .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y build-essential gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy your application code inside the container
COPY ./app ./app

# Expose port 8000 for FastAPI
EXPOSE 8000

# Create the database tables (optional, or handled on first run)
RUN python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Command to run FastAPI app with uvicorn and also run celery worker for async tasks
CMD ["sh", "-c", "celery -A app.celery_worker.celery worker --loglevel=info & uvicorn app.main:app --host 0.0.0.0 --port 8000"]
