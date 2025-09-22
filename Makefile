.PHONY: help dev prod build test clean

help:
	@echo "MenuMind AI - Available commands:"
	@echo "  make dev      - Start development environment"
	@echo "  make prod     - Start production environment"
	@echo "  make build    - Build all Docker images"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up containers and volumes"
	@echo "  make logs     - Show logs"
	@echo "  make shell    - Open Django shell"
	@echo "  make migrate  - Run database migrations"
	@echo "  make seed     - Seed database with initial data"

dev:
	docker-compose up

prod:
	docker-compose -f docker-compose.prod.yml up -d

build:
	docker-compose build

test:
	docker-compose run --rm backend python manage.py test
	docker-compose run --rm frontend npm test

clean:
	docker-compose down -v
	docker system prune -f

logs:
	docker-compose logs -f

shell:
	docker-compose exec backend python manage.py shell

migrate:
	docker-compose exec backend python manage.py migrate

seed:
	docker-compose exec backend python manage.py seed_data

backup:
	./scripts/backup.sh

restore:
	@read -p "Enter backup file path: " file; \
	./scripts/restore.sh $$file
