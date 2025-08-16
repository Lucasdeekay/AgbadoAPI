# AgbadoAPI

A comprehensive Django REST API for the Agbado platform, providing user management, wallet functionality, task rewards, service provider features, and real-time notifications with optimized performance and enhanced security.

## 🚀 Features

- **User Authentication & Management**: Secure user registration, login, and profile management with WebAuthn support
- **KYC (Know Your Customer)**: Document verification and user identity management
- **Wallet System**: Digital wallet with transaction tracking, Paystack integration, and balance management
- **Task & Reward System**: Daily tasks, point accumulation, and gift redemption
- **Service Provider Management**: Service provider registration and service management
- **Service Management**: Comprehensive service and subservice management with booking system
- **Notification System**: Real-time notifications for users
- **Social Media Integration**: Instagram and YouTube integration for leisure activities
- **WebAuthn Support**: Passwordless authentication using FIDO2/WebAuthn
- **Cloudinary Integration**: Secure file uploads and media management
- **Paystack Integration**: Payment processing and wallet funding
- **Termii Integration**: SMS notifications and OTP delivery

## 🛠️ Technology Stack

- **Backend**: Django 5.1.1, Django REST Framework 3.15.2
- **Database**: SQLite (Development), MySQL (Production)
- **Authentication**: Token Authentication, WebAuthn/FIDO2
- **File Storage**: Cloudinary
- **Real-time**: Django Channels with Redis
- **SMS**: Termii API
- **Payment**: Paystack Integration
- **Documentation**: DRF Auto-generated API docs
- **Code Quality**: Black, isort, flake8, mypy, pylint
- **Testing**: pytest, coverage, factory-boy
- **Security**: bandit, safety

## 📋 Prerequisites

- Python 3.8+
- Redis (for channels and caching)
- MySQL (for production)
- Cloudinary account
- Termii account
- Paystack account

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AgbadoAPI
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production)
DB_NAME=agbado_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587

# SMS Configuration (Termii)
TERMII_LIVE_KEY=your-termii-key

# Payment Configuration (Paystack)
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_PUBLIC_KEY=your-paystack-public-key

# WebAuthn Configuration
WEBAUTHN_RP_ID=localhost
WEBAUTHN_RP_NAME=AGBA-DO
WEBAUTHN_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Security Settings (for production)
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=
CORS_ALLOWED_ORIGIN_REGEXES=
```

### 5. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Redis (for channels)

```bash
redis-server
```

### 8. Start Development Server

```bash
python manage.py runserver
```

## 📁 Configuration Files

### Makefile

The `Makefile` provides comprehensive development commands:

```bash
# View all available commands
make help

# Installation & Setup
make install          # Install production dependencies
make install-dev      # Install development dependencies
make setup-dev        # Complete development environment setup
make setup-prod       # Complete production environment setup

# Testing & Quality
make test             # Run all tests
make test-coverage    # Run tests with coverage report
make lint             # Run linting tools
make format           # Format code with Black and isort
make check-all        # Run format, lint, and test
make security-check   # Run security vulnerability checks

# Database
make migrate          # Run database migrations
make makemigrations  # Create new migrations
make check-migrations # Check for pending migrations
make validate-models  # Validate Django models
make optimize-db      # Optimize database queries

# User Management
make superuser        # Create a Django superuser

# Development
make runserver        # Start development server
make shell            # Open Django shell
make collectstatic    # Collect static files

# Backup & Restore
make backup           # Backup database
make restore          # Restore database from backup
make backup-media     # Backup media files
make restore-media    # Restore media files

# Docker
make docker-build     # Build Docker image
make docker-run       # Run Docker container
make docker-compose-up    # Start with Docker Compose
make docker-compose-down  # Stop Docker Compose

# Maintenance
make clean            # Clean Python cache files
make check-deps       # Check for outdated dependencies
make update-deps      # Update dependencies
```

### pyproject.toml

The `pyproject.toml` file contains project metadata and tool configurations:

- **Project Information**: Version, description, authors, keywords
- **Dependencies**: Production and development dependencies with version constraints
- **Tool Configurations**: Black, isort, mypy, pytest, coverage, bandit, pylint
- **Python Support**: Python 3.8+ with Django 5.1+ support

### requirements-dev.txt

Development dependencies for testing, code quality, and development tools:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Or install with extras
pip install -e .[dev]
```

### setup.py

Package installation script with metadata:

```bash
# Install the package
pip install -e .

# Install with development dependencies
pip install -e .[dev]
```

## 📚 API Documentation

### Authentication Endpoints

- `POST /auth/register/` - User registration
- `POST /auth/login/` - User login
- `POST /auth/logout/` - User logout
- `POST /auth/send-otp/` - Send OTP for verification
- `POST /auth/verify-otp/` - Verify OTP
- `POST /auth/forgot-password/` - Forgot password
- `POST /auth/reset-password/` - Reset password
- `POST /auth/webauthn/register/` - WebAuthn registration
- `POST /auth/webauthn/authenticate/` - WebAuthn authentication

### User Management Endpoints

- `GET /user/dashboard/` - User dashboard
- `POST /user/profile/update/` - Update user profile
- `GET /user/kyc/` - Get KYC details
- `POST /user/kyc/update/` - Update KYC information
- `POST /user/change-password/` - Change password
- `GET /user/referral-code/` - Get referral code

### Task & Reward Endpoints

- `GET /user/api/tasks/` - List daily tasks
- `POST /user/api/task-completions/` - Complete a task
- `GET /user/api/rewards/` - User rewards
- `GET /user/api/user-activities/` - User activities
- `GET /user/api/gifts/` - Available gifts
- `POST /user/api/user-gifts/` - Claim a gift

### Wallet Endpoints

- `GET /wallet/balance/` - Get wallet balance
- `GET /wallet/transactions/` - Transaction history
- `GET /wallet/withdrawals/` - Withdrawal history
- `POST /wallet/withdraw/` - Withdraw funds
- `GET /wallet/banks/` - List available banks
- `POST /wallet/webhook/paystack/` - Paystack webhook

### Service Provider Endpoints

- `POST /provider/register/` - Service provider registration
- `GET /provider/services/` - List services
- `POST /provider/services/` - Create service
- `GET /provider/profile/` - Get provider profile
- `POST /provider/profile/update/` - Update provider profile

### Service Management Endpoints

- `GET /service/` - List all services
- `POST /service/` - Create a service
- `GET /service/{id}/` - Get service details
- `PUT /service/{id}/` - Update service
- `DELETE /service/{id}/` - Delete service
- `GET /service/subservices/` - List subservices
- `POST /service/subservices/` - Create subservice

### Service Request Endpoints

- `GET /service/requests/` - List service requests
- `POST /service/requests/` - Create service request
- `GET /service/requests/{id}/` - Get request details
- `PUT /service/requests/{id}/` - Update request
- `GET /service/requests/{id}/bids/` - List bids for request
- `POST /service/requests/{id}/bids/` - Submit bid

### Booking Endpoints

- `GET /service/bookings/` - List bookings
- `POST /service/bookings/` - Create booking
- `GET /service/bookings/{id}/` - Get booking details
- `PUT /service/bookings/{id}/` - Update booking

### Notification Endpoints

- `GET /notification/list/` - List notifications
- `POST /notification/mark-read/` - Mark notification as read
- `DELETE /notification/{id}/` - Delete notification
- `DELETE /notification/multiple/` - Delete multiple notifications

## 🔧 Development

### Code Style

This project follows PEP 8 style guidelines and uses Black for code formatting:

```bash
# Format code
make format

# Run linting
make lint

# Run all quality checks
make check-all
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Run specific test categories
pytest -m auth      # Authentication tests
pytest -m wallet    # Wallet tests
pytest -m service   # Service tests
pytest -m api       # API tests
```

### Database Migrations

```bash
# Create migrations
make makemigrations

# Apply migrations
make migrate

# Check migration status
make check-migrations
```

### Static Files

```bash
make collectstatic
```

### Security Checks

```bash
# Run security vulnerability checks
make security-check

# Check for outdated dependencies
make check-deps

# Update dependencies
make update-deps
```

## 🚀 Deployment

### Production Settings

1. Set `DEBUG=False` in your environment variables
2. Configure production database (MySQL recommended)
3. Set up proper CORS settings
4. Configure SSL/HTTPS
5. Set up proper logging
6. Configure Redis for production

### Environment Variables for Production

```env
DEBUG=False
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

### Docker Deployment

```bash
# Build Docker image
make docker-build

# Run Docker container
make docker-run

# Use Docker Compose
make docker-compose-up
```

## 📁 Project Structure

```
AgbadoAPI/
├── agbado/                 # Main project settings
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── auth_app/             # Authentication app
│   ├── models.py         # User and KYC models
│   ├── views.py          # Authentication views
│   ├── viewsets.py       # API ViewSets
│   ├── serializers.py    # User serializers
│   ├── admin.py          # Admin configuration
│   ├── tests.py          # Test suite
│   └── urls.py           # Auth URL patterns
├── user_app/             # User management app
│   ├── models.py         # Task, reward, activity models
│   ├── views.py          # User views
│   ├── viewsets.py       # API ViewSets
│   ├── serializers.py    # User serializers
│   ├── admin.py          # Admin configuration
│   ├── tests.py          # Test suite
│   └── urls.py           # User URL patterns
├── wallet_app/           # Wallet management app
│   ├── models.py         # Wallet, transaction models
│   ├── views.py          # Wallet views
│   ├── viewsets.py       # API ViewSets
│   ├── serializers.py    # Wallet serializers
│   ├── admin.py          # Admin configuration
│   ├── tests.py          # Test suite
│   └── urls.py           # Wallet URL patterns
├── service_app/          # Service management app
│   ├── models.py         # Service, booking models
│   ├── views.py          # Service views
│   ├── viewsets.py       # API ViewSets
│   ├── serializers.py    # Service serializers
│   ├── admin.py          # Admin configuration
│   ├── tests.py          # Test suite
│   └── urls.py           # Service URL patterns
├── provider_app/         # Service provider app
│   ├── models.py         # Provider models
│   ├── views.py          # Provider views
│   ├── viewsets.py       # API ViewSets
│   ├── serializers.py    # Provider serializers
│   ├── admin.py          # Admin configuration
│   ├── tests.py          # Test suite
│   └── urls.py           # Provider URL patterns
├── notification_app/     # Notification system
│   ├── models.py         # Notification models
│   ├── views.py          # Notification views
│   ├── viewsets.py       # API ViewSets
│   ├── serializers.py    # Notification serializers
│   ├── admin.py          # Admin configuration
│   ├── tests.py          # Test suite
│   └── urls.py           # Notification URL patterns
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── pyproject.toml       # Project metadata and tool configs
├── setup.py            # Package installation script
├── Makefile            # Development commands
├── manage.py           # Django management script
└── README.md           # This file
```

## 🔒 Security Features

- Token-based authentication
- CSRF protection
- XSS protection
- SQL injection prevention
- Rate limiting
- Secure file uploads
- Environment variable configuration
- HTTPS enforcement (production)
- WebAuthn/FIDO2 support
- Paystack webhook signature verification

## 📊 Monitoring & Logging

The application includes comprehensive logging:

- Request/response logging
- Error tracking
- User activity logging
- Performance monitoring
- Database query logging
- Security event logging

## 🧪 Testing

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Authentication Tests**: Login, registration, OTP
- **Wallet Tests**: Transaction, withdrawal, balance
- **Service Tests**: Service management, bookings
- **Provider Tests**: Provider registration, services

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test categories
pytest -m auth
pytest -m wallet
pytest -m service
pytest -m integration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks: `make check-all`
6. Submit a pull request

### Development Workflow

```bash
# Setup development environment
make setup-dev

# Make changes and run checks
make format lint test

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push changes
git push origin feature-branch
```

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Contact the development team
- Check the API documentation
- Review the troubleshooting guide

## 🔄 Version History

- **v1.0.0** - Initial release with core functionality
- **v1.1.0** - Added WebAuthn support
- **v1.2.0** - Enhanced security and performance optimizations
- **v1.3.0** - Comprehensive app optimization, enhanced admin interface, improved testing

## 📋 Configuration File Execution

### Makefile Commands

```bash
# View all commands
make help

# Quick setup
make setup-dev

# Development workflow
make format lint test

# Database management
make migrate
make backup
make restore

# Docker deployment
make docker-build
make docker-run
```

### pyproject.toml

This file is automatically used by tools like Black, isort, mypy, pytest, etc. No manual execution needed.

### requirements-dev.txt

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Or install with pip
pip install -r requirements-dev.txt
```

### setup.py

```bash
# Install the package
pip install -e .

# Install with development dependencies
pip install -e .[dev]

# Build distribution
python setup.py sdist bdist_wheel
```

---

**Note**: This is a development version. For production use, ensure all security measures are properly configured and all environment variables are set correctly. 