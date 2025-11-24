# Aeron

A local AI that captures conversations, stores them permanently, and uses RAG-based memory retrieval.

## Overview

Aeron is designed to be a "second brain" that runs entirely locally on a Raspberry Pi cluster (or similar hardware). It listens to audio, transcribes it, stores it, and allows you to query your past conversations using an LLM with RAG memory.

## Architecture

- **Transcription**: `faster-whisper` (real-time STT)
- **LLM**: Ollama running Llama 3.1 8B
- **Memory**: RAG system using ChromaDB and SentenceTransformers
- **Storage**: SQLite for structured data, filesystem for audio/transcripts
- **TTS**: Coqui TTS for voice cloning and response generation
- **UI**: Streamlit interface

## Setup

### Prerequisites

- Python 3.11+
- Poetry
- Docker
- Kubernetes (k3s recommended for Pi)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd aeron
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Download Models (Initial Setup):**
   Run the setup script to download Whisper, LLM, and TTS models (scripts to be added).

## Development

- **Linting**: `make lint`
- **Testing**: `make test`
- **Formatting**: `make format`

## Deployment

Deployment is managed via Helm charts.

```bash
make deploy
```

See `docs/DEPLOYMENT.md` for detailed instructions.

