FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/books data/processed data/embeddings logs

# Expose default port
EXPOSE 8080

# Run with uvicorn (using shell form to resolve $PORT variable)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
