.PHONY: dev test lint fmt clean docker-build docker-up

dev:
	uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app

lint:
	ruff check app/ tests/
	mypy app/

fmt:
	ruff format app/ tests/
	ruff check --fix app/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

seed:
	python scripts/seed_dialect_data.py
