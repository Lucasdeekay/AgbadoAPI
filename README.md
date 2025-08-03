# AgbadoAPI

A comprehensive Django REST API for the Agbado platform, providing user management, wallet functionality, task rewards, and service provider features.

## 🚀 Features

- **User Authentication & Management**: Secure user registration, login, and profile management
- **KYC (Know Your Customer)**: Document verification and user identity management
- **Wallet System**: Digital wallet with transaction tracking and balance management
- **Task & Reward System**: Daily tasks, point accumulation, and gift redemption
- **Service Provider Management**: Service provider registration and service management
- **Notification System**: Real-time notifications for users
- **Social Media Integration**: Instagram and YouTube integration for leisure activities
- **WebAuthn Support**: Passwordless authentication using FIDO2/WebAuthn
- **Cloudinary Integration**: Secure file uploads and media management

## 🛠️ Technology Stack

- **Backend**: Django 5.1.1, Django REST Framework 3.15.2
- **Database**: SQLite (Development), MySQL (Production)
- **Authentication**: Token Authentication, WebAuthn/FIDO2
- **File Storage**: Cloudinary
- **Real-time**: Django Channels with Redis
- **SMS**: Termii API
- **Payment**: Paystack Integration
- **Documentation**: DRF Auto-generated API docs

## 📋 Prerequisites

- Python 3.8+
- Redis (for channels and caching)
- MySQL (for production)
- Cloudinary account
- Termii account
- Paystack account

## 🚀 Installation

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
pip install -r requirements.txt
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

## 📚 API Documentation

### Authentication Endpoints

- `POST /auth/register/` - User registration
- `POST /auth/login/` - User login
- `POST /auth/logout/` - User logout
- `POST /auth/send-otp/` - Send OTP for verification
- `POST /auth/verify-otp/` - Verify OTP
- `POST /auth/forgot-password/` - Forgot password
- `POST /auth/reset-password/` - Reset password

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
- `POST /wallet/deposit/` - Deposit funds
- `POST /wallet/withdraw/` - Withdraw funds
- `GET /wallet/transactions/` - Transaction history

### Service Provider Endpoints

- `POST /provider/register/` - Service provider registration
- `GET /provider/services/` - List services
- `POST /provider/services/` - Create service
- `GET /service/requests/` - Service requests

### Notification Endpoints

- `GET /notification/list/` - List notifications
- `POST /notification/mark-read/` - Mark notification as read

## 🔧 Development

### Code Style

This project follows PEP 8 style guidelines and uses Black for code formatting:

```bash
# Install Black
pip install black

# Format code
black .
```

### Running Tests

```bash
python manage.py test
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Static Files

```bash
python manage.py collectstatic
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
│   ├── serializers.py    # User serializers
│   └── urls.py           # Auth URL patterns
├── user_app/             # User management app
│   ├── models.py         # Task, reward, activity models
│   ├── views.py          # User views
│   ├── viewsets.py       # API ViewSets
│   ├── serializers.py    # User serializers
│   └── urls.py           # User URL patterns
├── wallet_app/           # Wallet management app
├── service_app/          # Service management app
├── provider_app/         # Service provider app
├── notification_app/     # Notification system
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
└── README.md            # This file
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

## 📊 Monitoring & Logging

The application includes comprehensive logging:

- Request/response logging
- Error tracking
- User activity logging
- Performance monitoring
- Database query logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Contact the development team
- Check the API documentation

## 🔄 Version History

- **v1.0.0** - Initial release with core functionality
- **v1.1.0** - Added WebAuthn support
- **v1.2.0** - Enhanced security and performance optimizations

---

**Note**: This is a development version. For production use, ensure all security measures are properly configured. 