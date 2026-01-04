# Ollie

Local AI with total recall
Captures conversations, stores them permanently, and uses RAG-based memory retrieval.

## Overview

Ollie is designed to be a "second brain" that runs entirely locally on a Raspberry Pi cluster (or similar hardware). It listens to audio, transcribes it, stores it, and allows you to query your past conversations using an LLM with RAG memory.

## Architecture

- **Transcription**: `faster-whisper` (real-time STT with rolling window streaming)
- **LLM**: Ollama running Llama 3.1 8B
- **Memory**: RAG system using ChromaDB and SentenceTransformers
- **Storage**: SQLite for structured data, filesystem for audio/transcripts
- **TTS**: Coqui TTS for voice cloning and response generation
- **UI**: Streamlit interface (legacy) + React frontend (real-time transcription)

## Features

### Real-time Streaming Transcription

Ollie now supports real-time transcription with a rolling window approach:

- **WebSocket-based streaming**: Audio is streamed in real-time via WebSocket
- **Rolling window processing**: Continuous transcription with overlapping windows
- **React frontend**: Modern UI for real-time transcription
- **Incremental updates**: See transcriptions appear as you speak

See [docs/STREAMING_TRANSCRIPTION.md](docs/STREAMING_TRANSCRIPTION.md) for detailed documentation.

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
   cd ollie
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

## Real-time Transcription

To use the real-time transcription feature:

1. **Start the services:**
   ```bash
   # Using Make (recommended)
   make up
   
   # Or using docker compose directly
   docker compose -f docker-compose.local.yml up whisper core frontend
   ```

2. **Access the React frontend:**
   Open `http://localhost:3000` in your browser

3. **Click "Start Recording"** and speak into your microphone

The transcription will appear in real-time as you speak. When you stop recording, the transcription is automatically saved to the database and memory system.

For development, you can also run the frontend locally:
```bash
cd frontend
npm install
npm run dev
```

