# Ollie Frontend

React frontend for real-time transcription with WebSocket support.

## Development

```bash
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: `http://localhost:8000`)
- `VITE_WHISPER_WS_URL`: WebSocket URL for transcription (default: `ws://localhost:8000/ws/transcribe`)

## Build

```bash
npm run build
```

The built files will be in the `dist` directory.

