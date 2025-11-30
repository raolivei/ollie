# Ollie Master Plan

## Model Preference
**CRITICAL**: This project is being written with **gemini-3-pro**. Give preference to this model for all code generation, planning, and reasoning tasks within this project.

## Project Overview
Ollie is a local AI that captures conversations, stores them permanently, and uses RAG-based memory retrieval. It is designed to run on a Raspberry Pi cluster.

## Phase 1: Core Infrastructure Setup

### Goals
- Build core services (Whisper, Ollama, TTS, Memory).
- Set up RAG-based memory with ChromaDB.
- Create Streamlit UI.
- Deploy via Helm to Kubernetes (k3s).

### Architecture
- **Language**: Python 3.11+
- **Dependency Management**: Poetry
- **Containerization**: Docker (GHCR)
- **Orchestration**: Kubernetes (Helm)
- **Storage**: SQLite (Metadata), ChromaDB (Vectors), Filesystem (Audio)

### Component Stack
1. **Transcription**: `faster-whisper`
2. **LLM**: Ollama (Llama 3.1 8B)
3. **Memory**: ChromaDB + SentenceTransformers
4. **TTS**: Coqui TTS
5. **UI**: Streamlit
6. **Core**: FastAPI orchestrator

## Standards & Conventions
- Follow workspace `PROJECT_CONVENTIONS.md`.
- Use Helm for all deployments.
- Use Poetry for Python dependency management.
- Prioritize ARM64 compatibility for Raspberry Pi.

