FROM python:3.13.1-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create content directory if it doesn't exist
RUN mkdir -p content

# Create a volume for content and data
VOLUME ["/app/content", "/app/data"]

# Expose the port the app runs on
EXPOSE 5001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=development

# Command to run the application
CMD ["python", "main.py"]
