# Makefile for AgbadoAPI
# Comprehensive development tasks and commands for the optimized project

.PHONY: help install install-dev test test-coverage lint format clean migrate superuser runserver shell collectstatic makemigrations security-check check-all setup-dev setup-prod backup restore docker-build docker-run docker-compose-up docker-compose-down check-migrations validate-models optimize-db backup-media restore-media check-deps update-deps

# Default target
help:
	@echo "🚀 AgbadoAPI Development Commands"
	@echo ""
	@echo "📦 Installation & Setup:"
	@echo "  install         - Install production dependencies"
	@echo "  install-dev     - Install development dependencies"
	@echo "  setup-dev       - Complete development environment setup"
	@echo "  setup-prod      - Complete production environment setup"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  test            - Run all tests"
	@echo "  test-coverage   - Run tests with coverage report"
	@echo "  lint            - Run linting tools (flake8, pylint, mypy)"
	@echo "  format          - Format code with Black and isort"
	@echo "  check-all       - Run format, lint, and test"
	@echo "  security-check  - Run security vulnerability checks"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  migrate         - Run database migrations"
	@echo "  makemigrations  - Create new migrations"
	@echo "  check-migrations - Check for pending migrations"
	@echo "  validate-models - Validate Django models"
	@echo "  optimize-db     - Optimize database queries"
	@echo ""
	@echo "👤 User Management:"
	@echo "  superuser       - Create a Django superuser"
	@echo ""
	@echo "🖥️  Development:"
	@echo "  runserver       - Start development server"
	@echo "  shell           - Open Django shell"
	@echo "  collectstatic   - Collect static files"
	@echo ""
	@echo "💾 Backup & Restore:"
	@echo "  backup          - Backup database"
	@echo "  restore         - Restore database from backup"
	@echo "  backup-media    - Backup media files"
	@echo "  restore-media   - Restore media files"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-build    - Build Docker image"
	@echo "  docker-run      - Run Docker container"
	@echo "  docker-compose-up   - Start with Docker Compose"
	@echo "  docker-compose-down - Stop Docker Compose"
	@echo ""
	@echo "🔧 Maintenance:"
	@echo "  clean           - Clean Python cache files"
	@echo "  check-deps      - Check for outdated dependencies"
	@echo "  update-deps     - Update dependencies"

# Installation commands
install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Testing commands
test:
	@echo "🧪 Running tests..."
	python manage.py test --verbosity=2

test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=. --cov-report=html --cov-report=term --cov-fail-under=80

# Code quality commands
lint:
	@echo "🔍 Running linting tools..."
	flake8 . --max-line-length=88 --extend-ignore=E203,W503
	pylint **/*.py --disable=C0114,C0115,C0116,R0903,R0913,W0621,W0612,W0611
	mypy . --ignore-missing-imports

format:
	@echo "🎨 Formatting code..."
	black . --line-length=88
	isort . --profile=black --line-length=88

# Database commands
migrate:
	@echo "🗄️ Running database migrations..."
	python manage.py makemigrations
	python manage.py migrate

makemigrations:
	@echo "🗄️ Creating new migrations..."
	python manage.py makemigrations

check-migrations:
	@echo "🔍 Checking for pending migrations..."
	python manage.py showmigrations

validate-models:
	@echo "🔍 Validating Django models..."
	python manage.py check --deploy

optimize-db:
	@echo "⚡ Optimizing database..."
	python manage.py dbshell --command="VACUUM ANALYZE;"

# User management
superuser:
	@echo "👤 Creating superuser..."
	python manage.py createsuperuser

# Development commands
runserver:
	@echo "🖥️ Starting development server..."
	python manage.py runserver

shell:
	@echo "🐍 Opening Django shell..."
	python manage.py shell

collectstatic:
	@echo "📁 Collecting static files..."
	python manage.py collectstatic --noinput

# Security and quality checks
security-check:
	@echo "🔒 Running security checks..."
	bandit -r . --exclude-dir=tests,migrations
	safety check

check-all: format lint test
	@echo "✅ All checks completed!"

# Setup commands
setup-dev: install-dev migrate superuser
	@echo "✅ Development environment setup complete!"

setup-prod: install migrate collectstatic
	@echo "✅ Production environment setup complete!"

# Backup and restore commands
backup:
	@echo "💾 Creating database backup..."
	python manage.py dumpdata --exclude=contenttypes --exclude=auth.Permission > backup_$(shell date +%Y%m%d_%H%M%S).json

restore:
	@echo "📥 Restoring database from backup..."
	python manage.py loaddata backup_*.json

backup-media:
	@echo "💾 Creating media backup..."
	tar -czf media_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz media/

restore-media:
	@echo "📥 Restoring media files..."
	tar -xzf media_backup_*.tar.gz

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t agbado-api .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 8000:8000 agbado-api

docker-compose-up:
	@echo "🐳 Starting with Docker Compose..."
	docker-compose up -d

docker-compose-down:
	@echo "🐳 Stopping Docker Compose..."
	docker-compose down

# Maintenance commands
clean:
	@echo "🧹 Cleaning Python cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/

check-deps:
	@echo "🔍 Checking for outdated dependencies..."
	pip list --outdated

update-deps:
	@echo "📦 Updating dependencies..."
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt

# Additional utility commands
check-logs:
	@echo "📋 Checking application logs..."
	tail -f logs/django.log

check-status:
	@echo "📊 Checking application status..."
	@echo "Database migrations:"
	@python manage.py showmigrations | grep -E "\[ \]|\[X\]" || true
	@echo ""
	@echo "Static files:"
	@python manage.py collectstatic --dry-run --verbosity=0 || true
	@echo ""
	@echo "Environment variables:"
	@python manage.py check --deploy 2>&1 | grep -E "WARN|ERROR" || echo "No warnings or errors found"

# Performance monitoring
profile:
	@echo "📊 Starting performance profiling..."
	python manage.py runserver --noreload &
	@echo "Server started. Use Ctrl+C to stop profiling."
	@python -m cProfile -o profile_output.prof manage.py runserver --noreload

analyze-profile:
	@echo "📊 Analyzing performance profile..."
	python -c "import pstats; p = pstats.Stats('profile_output.prof'); p.sort_stats('cumulative').print_stats(20)"

# Documentation
docs:
	@echo "📚 Building documentation..."
	cd docs && make html

serve-docs:
	@echo "📚 Serving documentation..."
	cd docs/_build/html && python -m http.server 8001

# Database management
reset-db:
	@echo "⚠️  Resetting database (this will delete all data!)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		python manage.py flush --noinput; \
		python manage.py migrate; \
		echo "Database reset complete!"; \
	else \
		echo "Database reset cancelled."; \
	fi

# Environment management
create-env:
	@echo "🌍 Creating virtual environment..."
	python -m venv .venv
	@echo "Virtual environment created. Activate it with:"
	@echo "source .venv/bin/activate  # On Unix/macOS"
	@echo ".venv\\Scripts\\activate     # On Windows"

activate-env:
	@echo "🌍 Activating virtual environment..."
	@echo "Run: source .venv/bin/activate  # On Unix/macOS"
	@echo "Run: .venv\\Scripts\\activate     # On Windows"

# Git utilities
pre-commit: format lint test
	@echo "✅ Pre-commit checks passed!"

git-hooks:
	@echo "🔗 Setting up git hooks..."
	@if [ -d .git ]; then \
		echo '#!/bin/sh' > .git/hooks/pre-commit; \
		echo 'make pre-commit' >> .git/hooks/pre-commit; \
		chmod +x .git/hooks/pre-commit; \
		echo "Git hooks configured!"; \
	else \
		echo "Not a git repository!"; \
	fi 