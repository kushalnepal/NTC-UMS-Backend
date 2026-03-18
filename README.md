# NTC User Management System - Backend

A robust Django REST API backend for the NTC User Management System, providing secure authentication, user management, and organization hierarchy features.

[![Django](https://img.shields.io/badge/Django-6.0-green)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![DRF](https://img.shields.io/badge/Django%20REST%20Framework-3.15-red)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🚀 Features

### User Authentication

- JWT-based authentication using djangorestframework-simplejwt
- Custom user model with extended fields
- Secure password hashing
- Login/Logout functionality

### User Management

- Create, Read, Update, Delete users
- Role-based permissions
- User search and filtering
- Profile management

### Organization Management

- Hierarchical organization structure
- Department management
- Employee-organization relationships

### API Features

- RESTful API design
- Token-based authentication
- CORS support for frontend integration
- Comprehensive API endpoints

## 🛠️ Tech Stack

- **Framework:** Django 6.0
- **Language:** Python 3.10+
- **API:** Django REST Framework
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Database:** SQLite (development) / PostgreSQL (production)
- **CORS:** django-cors-headers

## 📋 Prerequisites

Before running this project, ensure you have the following installed:

- Python (3.10 or higher)
- pip or poetry

## 🔧 Installation

Clone the repository:

```bash
git clone <repository-url>
cd python
```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
# Create .env file (optional)
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

Run migrations:

```bash
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open http://localhost:8000 in your browser.

## 🏗️ Project Structure

```
python/
├── accounts/                   # User authentication app
│   ├── migrations/            # Database migrations
│   ├── management/            # Custom management commands
│   │   └── commands/          # Custom Django commands
│   ├── admin.py              # Django admin configuration
│   ├── auth_backends.py      # Custom authentication
│   ├── managers.py           # Custom user managers
│   ├── models.py             # User models
│   ├── permissions.py        # Custom permissions
│   ├── serializers.py        # DRF serializers
│   ├── urls.py               # URL routing
│   └── views.py              # API views
├── organization/              # Organization app
│   ├── migrations/
│   ├── admin.py
│   ├── models.py             # Organization models
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── storefront/               # Django project settings
│   ├── asgi.py
│   ├── settings.py           # Main settings
│   ├── urls.py               # Root URL configuration
│   └── wsgi.py
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
└── db.sqlite3               # SQLite database
```

## 📡 API Endpoints

### Authentication

| Method | Endpoint                   | Description         |
| ------ | -------------------------- | ------------------- |
| POST   | `/api/auth/register/`      | Register a new user |
| POST   | `/api/auth/login/`         | User login          |
| POST   | `/api/auth/logout/`        | User logout         |
| POST   | `/api/auth/token/`         | Obtain JWT token    |
| POST   | `/api/auth/token/refresh/` | Refresh JWT token   |

### Users

| Method | Endpoint                | Description      |
| ------ | ----------------------- | ---------------- |
| GET    | `/api/auth/users/`      | List all users   |
| GET    | `/api/auth/users/{id}/` | Get user details |
| PUT    | `/api/auth/users/{id}/` | Update user      |
| DELETE | `/api/auth/users/{id}/` | Delete user      |

### Organizations

| Method | Endpoint                       | Description                |
| ------ | ------------------------------ | -------------------------- |
| GET    | `/api/organization/hierarchy/` | Get organization hierarchy |
| GET    | `/api/organization/`           | List organizations         |
| POST   | `/api/organization/`           | Create organization        |

## 🔐 Authentication

This API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token-here>
```

### Obtaining a Token

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

### Refreshing a Token

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your-refresh-token"}'
```

## 🧪 Testing

Run the development server with test data:

```bash
# Seed the database with test data
python manage.py seed_data

# Run tests
python manage.py test
```

## 🔧 Management Commands

- `python manage.py createsuperuser` - Create admin user
- `python manage.py seed_data` - Populate database with sample data
- `python manage.py migrate` - Apply database migrations
- `python manage.py makemigrations` - Create new migrations

## 🚢 Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn storefront.wsgi:application --bind 0.0.0.0:8000
```

### Using Docker

Create a Dockerfile:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### Production Settings

Update `storefront/settings.py` for production:

```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
SECRET_KEY = os.environ.get('SECRET_KEY')
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

Your Name - [GitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)

---

Built with ❤️ using Django
