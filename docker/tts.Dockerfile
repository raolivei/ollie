FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for TTS (libsndfile, espeak, rust for sudachipy)
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    espeak-ng \
    git \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only main,tts --no-interaction --no-ansi --no-root

# Agree to Coqui license
ENV COQUI_TOS_AGREED=1

# Copy application code
COPY src/ /app/src/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "aeron.tts.api:app", "--host", "0.0.0.0", "--port", "8000"]
