.PHONY: install test lint format clean build deploy up down

install:
	poetry install
	pre-commit install

test:
	poetry run pytest tests/

lint:
	poetry run ruff check .
	poetry run mypy src/

format:
	poetry run black .
	poetry run isort .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	docker build -t ghcr.io/raolivei/ollie-whisper -f docker/whisper.Dockerfile .
	docker build -t ghcr.io/raolivei/ollie-ollama -f docker/ollama.Dockerfile .
	docker build -t ghcr.io/raolivei/ollie-tts -f docker/tts.Dockerfile .
	docker build -t ghcr.io/raolivei/ollie-core -f docker/core.Dockerfile .
	docker build -t ghcr.io/raolivei/ollie-ui -f docker/ui.Dockerfile .
	docker build -t ghcr.io/raolivei/ollie-training -f docker/training.Dockerfile .

deploy:
	helm upgrade --install ollie helm/ollie --namespace ollie --create-namespace

up:
	docker compose -f docker-compose.local.yml up -d whisper core frontend

down:
	docker compose -f docker-compose.local.yml down
