FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only main,whisper --no-interaction --no-ansi --no-root

# Copy application code
COPY src/ /app/src/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "aeron.transcription.api:app", "--host", "0.0.0.0", "--port", "8000"]
