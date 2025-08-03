# Makefile for AgbadoAPI
# Common development tasks and commands

.PHONY: help install test lint format clean migrate superuser runserver shell

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting tools"
	@echo "  format      - Format code with Black"
	@echo "  clean       - Clean Python cache files"
	@echo "  migrate     - Run database migrations"
	@echo "  superuser   - Create a superuser"
	@echo "  runserver   - Start development server"
	@echo "  shell       - Open Django shell"
	@echo "  collectstatic - Collect static files"
	@echo "  makemigrations - Create new migrations"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Run tests
test:
	python manage.py test --verbosity=2

# Run tests with coverage
test-coverage:
	pytest --cov=. --cov-report=html --cov-report=term

# Run linting tools
lint:
	flake8 .
	pylint **/*.py
	mypy .

# Format code
format:
	black .
	isort .

# Clean Python cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/

# Run database migrations
migrate:
	python manage.py makemigrations
	python manage.py migrate

# Create superuser
superuser:
	python manage.py createsuperuser

# Start development server
runserver:
	python manage.py runserver

# Open Django shell
shell:
	python manage.py shell

# Collect static files
collectstatic:
	python manage.py collectstatic --noinput

# Create new migrations
makemigrations:
	python manage.py makemigrations

# Check for security vulnerabilities
security-check:
	bandit -r .
	safety check

# Run all checks (format, lint, test)
check-all: format lint test

# Setup development environment
setup-dev: install migrate superuser

# Production setup
setup-prod: install migrate collectstatic

# Backup database
backup:
	python manage.py dumpdata > backup_$(shell date +%Y%m%d_%H%M%S).json

# Load database backup
restore:
	python manage.py loaddata backup_*.json

# Docker commands
docker-build:
	docker build -t agbado-api .

docker-run:
	docker run -p 8000:8000 agbado-api

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down 