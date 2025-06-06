FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml .

# Install dependencies using uv
RUN uv pip install .

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8000
ENV ENV=production

# Run the application
CMD exec gunicorn --bind :$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 0 main:app 