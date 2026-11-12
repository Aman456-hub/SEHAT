# Use lightweight official Python base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend codebase (we assume the build context is set to the sehat root or backend folder)
# To preserve the python module structure (backend.main), we copy it into a folder named backend
COPY . ./backend

# Expose port 8000 for FastAPI
EXPOSE 8000

# Execute uvicorn server on startup
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
