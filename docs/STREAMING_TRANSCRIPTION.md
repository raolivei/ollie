# Real-time Streaming Transcription with Rolling Window

This document describes the implementation of real-time transcription with WebSocket support and rolling window processing.

## Overview

The rolling window transcription feature allows users to speak continuously while receiving real-time transcription updates. The system processes audio in overlapping windows to provide incremental transcriptions without waiting for the user to finish speaking.

## Architecture

### Components

1. **React Frontend** (`frontend/`)
   - Captures audio from the user's microphone
   - Streams audio chunks via WebSocket
   - Displays real-time transcription updates
   - Saves final transcription to the backend

2. **Whisper Service** (`src/ollie/transcription/`)
   - WebSocket endpoint: `/ws/transcribe`
   - Streaming transcription service with rolling window
   - Processes audio chunks in real-time

3. **Core Service** (`src/ollie/core/`)
   - Endpoint to save streaming transcriptions: `/save_streaming_transcription`
   - Stores transcriptions in database and memory system

## How It Works

### Rolling Window Approach

1. **Audio Buffering**: Audio chunks are continuously added to a rolling buffer
2. **Window Processing**: When enough audio is buffered (default: 5 seconds), transcription begins
3. **Overlap**: Windows overlap by 1 second to avoid cutting words in the middle
4. **Incremental Updates**: New transcriptions are sent to the client as they're generated
5. **Deduplication**: The system tracks the last transcription to avoid sending duplicate text

### WebSocket Protocol

**Client → Server:**
- First message: Session ID (text)
- Subsequent messages: Audio chunks (binary, PCM 16-bit, 16kHz mono)

**Server → Client:**
- `{"type": "session_started", "session_id": "..."}`
- `{"type": "transcription_update", "text": "...", "full_text": "...", "is_final": false}`
- `{"type": "transcription_final", "text": "...", "is_final": true}`
- `{"type": "error", "message": "..."}`

## Configuration

### Backend (Whisper Service)

The `StreamingTranscriptionService` can be configured with:

- `model_size`: Whisper model size (tiny, base, small, medium, large-v2)
- `window_size_seconds`: Size of rolling window (default: 5.0 seconds)
- `overlap_seconds`: Overlap between windows (default: 1.0 second)
- `sample_rate`: Audio sample rate (default: 16000 Hz)

### Frontend

Environment variables:

- `VITE_API_URL`: Backend API URL (default: `http://localhost:8000`)
- `VITE_WHISPER_WS_URL`: WebSocket URL (default: `ws://localhost:8000/ws/transcribe`)

## Usage

### Development

1. **Start Backend Services:**
   ```bash
   docker-compose up whisper core
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access UI:**
   Open `http://localhost:3000` in your browser

### Production

The frontend is containerized and can be deployed with:

```bash
docker-compose up frontend
```

The frontend will be available at `http://localhost:3000` (or configured port).

## Technical Details

### Audio Processing

- **Format**: PCM 16-bit, mono, 16kHz
- **Chunk Size**: 4096 samples per chunk
- **Buffer**: Rolling buffer with max size of `window_size_samples + overlap_samples`

### Transcription

- Uses `faster-whisper` for efficient transcription
- VAD (Voice Activity Detection) enabled
- Auto language detection
- Beam size: 5

### Performance Considerations

- Transcription runs in an executor to avoid blocking the event loop
- Only one transcription task runs per session at a time
- Old transcription tasks are cancelled when new audio arrives
- Final transcription is sent when the session ends

## Future Improvements

- [ ] Adaptive window sizing based on speech patterns
- [ ] Speaker diarization for multi-speaker scenarios
- [ ] Language detection and switching
- [ ] Compression for audio chunks
- [ ] Reconnection handling for dropped connections
- [ ] Quality metrics and monitoring

