.PHONY: install test lint format clean build deploy

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
	docker build -t ghcr.io/raolivei/aeron-whisper -f docker/whisper.Dockerfile .
	docker build -t ghcr.io/raolivei/aeron-ollama -f docker/ollama.Dockerfile .
	docker build -t ghcr.io/raolivei/aeron-tts -f docker/tts.Dockerfile .
	docker build -t ghcr.io/raolivei/aeron-core -f docker/core.Dockerfile .
	docker build -t ghcr.io/raolivei/aeron-ui -f docker/ui.Dockerfile .
	docker build -t ghcr.io/raolivei/aeron-training -f docker/training.Dockerfile .

deploy:
	helm upgrade --install aeron helm/aeron --namespace aeron --create-namespace
