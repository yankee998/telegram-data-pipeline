# Use official Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2-binary
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pip cache and requirements file
COPY pip-cache /pip-cache
COPY requirements.txt .

# Install dependencies from local cache
RUN pip install --no-index --find-links=/pip-cache --prefer-binary -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run the application (placeholder)
CMD ["python", "main.py"]