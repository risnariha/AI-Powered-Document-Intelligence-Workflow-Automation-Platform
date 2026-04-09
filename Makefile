.PHONY: help setup dev start stop clean test logs

help:
	@echo "Available commands:"
	@echo "  make setup    - Install dependencies"
	@echo "  make dev      - Start development environment"
	@echo "  make start    - Start all services"
	@echo "  make stop     - Stop all services"
	@echo "  make clean    - Clean up containers and volumes"
	@echo "  make test     - Run tests"
	@echo "  make logs     - View logs"

setup:
	@echo "Installing Python dependencies..."
	cd backend-fastapi && pip install -r requirements.txt
	@echo "Setup complete"

dev:
	@echo "Starting development environment..."
	docker-compose up -d postgres redis qdrant
	@echo "Starting FastAPI backend..."
	cd backend-fastapi && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

start:
	docker-compose up -d

stop:
	docker-compose down

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

test:
	cd backend-fastapi && pytest -v

logs:
	docker-compose logs -f

shell-db:
	docker-compose exec postgres psql -U user -d docintel

shell-redis:
	docker-compose exec redis redis-cli