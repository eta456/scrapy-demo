# Use an official lightweight Python image
FROM python:3.13-slim

# Set environment variables to prevent Python from writing .pyc files and to ensure output is flushed immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies required for Scrapy, lxml, and curl_cffi
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (to leverage Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project code
COPY . .

# Create a non-root user for security
RUN useradd -m scraperuser && chown -R scraperuser /app
USER scraperuser

# Default command to run your spider
CMD ["scrapy", "crawl", "bunnings"]