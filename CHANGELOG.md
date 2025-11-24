# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-24

### Added
- Initial project scaffold with Poetry and standard configs.
- Core services: Whisper (STT), Ollama (LLM), Coqui (TTS).
- Storage layer: SQLAlchemy models and SQLite database.
- Memory system: RAG with ChromaDB and SentenceTransformers.
- User Interface: Streamlit app for chat and history.
- Infrastructure: Helm charts for all components.
- CI/CD: GitHub Actions for testing and GHCR publishing.
- Documentation: MASTER_PROMPT and project rules.
- Deployment script `scripts/deploy-eldertree.sh` for Pi cluster.

### Fixed
- Docker build failures on ARM64 by installing Rust for TTS service.
- Optimized Docker builds by separating Poetry dependency groups (Whisper, TTS, Core, UI).
- Removed unnecessary audio capture dependencies (pyaudio) from Whisper container.
