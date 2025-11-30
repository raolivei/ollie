FROM python:3.11-slim

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python ML deps
# Note: On Pi 5 (ARM64), torch installation might need specific index or pre-built wheels
# We use standard pip, which should find aarch64 wheels for torch
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install transformers peft trl datasets bitsandbytes scipy

# Clone llama.cpp for conversion scripts (if needed)
RUN git clone https://github.com/ggerganov/llama.cpp /app/llama.cpp && \
    cd /app/llama.cpp && \
    pip install -r requirements.txt

# Copy Ollie code
COPY pyproject.toml ./
# We might need to install ollie deps too if we import from it
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root

COPY src/ /app/src/
ENV PYTHONPATH=/app/src

CMD ["python", "/app/src/ollie/training/train.py"]
