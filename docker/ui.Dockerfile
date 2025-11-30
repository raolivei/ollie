FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --only main,ui --no-interaction --no-ansi --no-root

# Copy application code
COPY src/ /app/src/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "src/ollie/ui/app.py", "--server.address=0.0.0.0"]
