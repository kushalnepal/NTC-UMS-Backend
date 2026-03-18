# NTC User Management System - Backend

A robust Django REST API backend for the NTC User Management System, providing secure authentication, multi-level organization hierarchy, role-based access control, and comprehensive user management.

[![Django](https://img.shields.io/badge/Django-6.0-green)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![DRF](https://img.shields.io/badge/Django%20REST%20Framework-3.15-red)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🚀 Features

### User Authentication

- JWT-based authentication using djangorestframework-simplejwt
- Custom user model supporting username, email, and phone login
- Secure password hashing
- Login/Logout functionality with token refresh
- Multi-domain support in tokens

### Admin Request System

- Public endpoint for requesting admin access to organizations
- Support for requesting admin role at Organization, Department, or Wing level
- Automatic membership creation upon approval

### Multi-Level Organization Hierarchy

- **Domain** - Root level (e.g., "NTC")
- **Organization** - Companies under a domain (e.g., "NTC Telecom")
- **Department** - Departments within an organization (e.g., "IT Department")
- **Wing** - Sub-units within departments (e.g., "Software Wing")

### Role-Based Access Control

- **Admin** - Full CRUD permissions on users and hierarchy
- **User** - Read-only access to hierarchy data
- Custom roles with JSON permissions support
- Generic Foreign Key for flexible entity relationships

### User Management

- Create, Read, Update, Delete users
- User profile management
- Multi-membership support (users can belong to multiple entities)
- User search and filtering

### API Features

- RESTful API design
- Token-based authentication (JWT)
- CORS support for frontend integration
- Comprehensive API endpoints for all entities

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
│   ├── models.py             # Organization models (Domain, Organization, Department, Wing, Role, Membership)
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

| Method | Endpoint                      | Description                                |
| ------ | ----------------------------- | ------------------------------------------ |
| POST   | `/api/v1/auth/signup/`        | Register a new user with membership        |
| POST   | `/api/v1/auth/login/`         | User login (supports username/email/phone) |
| POST   | `/api/v1/auth/admin-request/` | Request admin access to an entity          |
| POST   | `/api/v1/auth/token/`         | Obtain JWT token                           |
| POST   | `/api/v1/auth/token/refresh/` | Refresh JWT token                          |
| POST   | `/api/v1/auth/token/verify/`  | Verify JWT token                           |

### Hierarchy

| Method | Endpoint                                    | Description                         |
| ------ | ------------------------------------------- | ----------------------------------- |
| GET    | `/api/v1/auth/hierarchy/`                   | Get user's accessible hierarchy     |
| GET    | `/api/v1/auth/hierarchy-members/`           | Get all members in user's hierarchy |
| POST   | `/api/v1/auth/hierarchy-members/`           | Create user (Admin only)            |
| PUT    | `/api/v1/auth/hierarchy-members/<user_id>/` | Update user (Admin only)            |
| DELETE | `/api/v1/auth/hierarchy-members/<user_id>/` | Delete user (Admin only)            |

### Users

| Method | Endpoint                   | Description      |
| ------ | -------------------------- | ---------------- |
| GET    | `/api/v1/auth/users/`      | List all users   |
| GET    | `/api/v1/auth/users/{id}/` | Get user details |
| POST   | `/api/v1/auth/users/`      | Create user      |
| PUT    | `/api/v1/auth/users/{id}/` | Update user      |
| DELETE | `/api/v1/auth/users/{id}/` | Delete user      |

### Organization

| Method | Endpoint                              | Description               |
| ------ | ------------------------------------- | ------------------------- |
| GET    | `/api/v1/domains/`                    | List all domains          |
| POST   | `/api/v1/domains/`                    | Create domain             |
| GET    | `/api/v1/organizations/`              | List organizations        |
| POST   | `/api/v1/organizations/`              | Create organization       |
| GET    | `/api/v1/departments/`                | List departments          |
| POST   | `/api/v1/departments/`                | Create department         |
| GET    | `/api/v1/departments/{id}/hierarchy/` | Get department with wings |
| GET    | `/api/v1/wings/`                      | List wings                |
| POST   | `/api/v1/wings/`                      | Create wing               |
| GET    | `/api/v1/roles/`                      | List roles                |
| POST   | `/api/v1/roles/`                      | Create role               |
| GET    | `/api/v1/memberships/`                | List memberships          |
| POST   | `/api/v1/memberships/`                | Create membership         |

## 🔐 Authentication

This API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token-here>
```

### Obtaining a Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

### Refreshing a Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your-refresh-token"}'
```

## 📊 Data Models

### User

- `id` (UUID)
- `username` (unique, optional)
- `email` (unique, optional)
- `phone` (unique, optional)
- `is_active`, `is_staff`, `is_superuser`
- `date_joined`

### Organization Hierarchy

- **Domain**: Root entity (e.g., "NTC")
- **Organization**: Belongs to Domain (e.g., "NTC Telecom")
- **Department**: Belongs to Organization
- **Wing**: Belongs to Department

### Role & Membership

- **Role**: Name + JSON permissions
- **Membership**: Links User to any entity (Domain/Organization/Department/Wing) with a Role

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

Kushal Nepal - [GitHub](https://github.com/kushalnepal)

## 🙏 Acknowledgments

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)

---

Built with ❤️ using Django
