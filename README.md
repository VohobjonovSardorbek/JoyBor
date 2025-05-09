# Dormitory Management System

A comprehensive web-based system for managing university dormitories, built with Django and Django REST Framework.

## Features

### User Management
- Multi-role system (Super Admin, Dormitory Admin, Student)
- Secure authentication with JWT tokens
- Password reset functionality
- User profile management
- Role-based access control

### Dormitory Management
- University management
- Dormitory facility management
- Floor and room management
- Room type and facility configuration
- Picture management for dormitories and rooms

### Student Management
- Student profile management
- Application system for dormitory rooms
- Document management for applications
- Application status tracking

### Booking System
- Room booking management
- Booking status tracking
- Room availability checking

### Payment System
- Multiple payment type support
- Payment status tracking
- Transaction history
- Subscription management

## API Documentation

The API documentation is available in multiple formats:
- Swagger UI: `/docs/`
- ReDoc: `/redoc/`
- OpenAPI JSON: `/swagger.json`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dormitory-management
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `DATABASE_URL`: Database connection URL
- `JWT_SECRET_KEY`: JWT signing key
- `EMAIL_HOST`: SMTP server host
- `EMAIL_PORT`: SMTP server port
- `EMAIL_HOST_USER`: SMTP username
- `EMAIL_HOST_PASSWORD`: SMTP password

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Testing

Run the test suite:
```bash
python manage.py test
```

Run specific app tests:
```bash
python manage.py test payment
python manage.py test dormitory
python manage.py test student
```

## API Endpoints

### User Management
- `/api/users/` - User management endpoints
- `/api/users/register/` - User registration
- `/api/users/login/` - User login
- `/api/users/reset-password/` - Password reset

### Dormitory Management
- `/api/dormitory/` - All dormitory-related endpoints
  - `/universities/` - University management
  - `/dormitories/` - Dormitory management
  - `/floors/` - Floor management
  - `/rooms/` - Room management
  - `/room-types/` - Room type management
  - `/room-facilities/` - Room facility management
  - `/bookings/` - Booking management

### Student Management
- `/api/student/` - Student profile management
- `/api/student/applications/` - Application management
- `/api/student/documents/` - Document management

### Payment Management
- `/api/payment/` - Payment management endpoints
  - `/transactions/` - Payment transaction management
  - `/subscriptions/` - Subscription management
  - `/statistics/` - Payment statistics

## Security

- JWT-based authentication with refresh tokens
- Role-based access control
- Password hashing
- Secure password reset flow
- Protected API endpoints
- Rate limiting on sensitive endpoints
- CORS configuration
- XSS protection
- SQL injection protection

## Deployment

1. Set up a production server (e.g., Gunicorn)
2. Configure a reverse proxy (e.g., Nginx)
3. Set up SSL/TLS certificates
4. Configure production environment variables
5. Set up database backups
6. Configure monitoring and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the BSD License - see the LICENSE file for details.

## Contact

For any queries, please contact: contact@dormitory.com 