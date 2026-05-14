.PHONY: help dev down logs ps migrate revision shell-api shell-db build clean

help:
	@echo "Targets:"
	@echo "  dev          Bring up the full local stack (postgres, redis, api, worker, web)"
	@echo "  down         Stop the stack"
	@echo "  logs         Tail logs from all services"
	@echo "  ps           Show running services"
	@echo "  migrate      Run Alembic migrations against the local DB"
	@echo "  revision m=  Create a new Alembic revision (m=\"message\")"
	@echo "  shell-api    Open a shell in the api container"
	@echo "  shell-db     Open a psql shell against the local DB"
	@echo "  build        Rebuild all images"
	@echo "  clean        Remove containers + local data volumes"

dev:
	docker compose up -d
	@echo "API:  http://localhost:8000/health"
	@echo "Web:  http://localhost:3000"

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

migrate:
	docker compose run --rm api alembic upgrade head

revision:
	@test -n "$(m)" || (echo "usage: make revision m=\"your message\"" && exit 1)
	docker compose run --rm api alembic revision --autogenerate -m "$(m)"

shell-api:
	docker compose exec api bash

shell-db:
	docker compose exec postgres psql -U agency -d agency

build:
	docker compose build

clean:
	docker compose down -v
	rm -rf .docker-data
