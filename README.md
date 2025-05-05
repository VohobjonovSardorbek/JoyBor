# JoyBor - Dormitory Management System

A comprehensive dormitory management system built with Django REST Framework.

## Features

- User authentication and authorization with JWT
- Role-based access control (Super Admin, Dormitory Admin, Student)
- Dormitory management
- Room booking system
- Payment integration
- Student profile management
- API documentation with Swagger

## Prerequisites

- Python 3.8+
- PostgreSQL
- Node.js (for frontend development)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/joybor.git
cd joybor
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

4. Create a `.env` file:
```bash
cp .env.example .env
```
Edit the `.env` file with your configuration.

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

## API Documentation

- Swagger UI: http://localhost:8000/docs/
- ReDoc: http://localhost:8000/redoc/

## Project Structure

```
joybor/
├── users/           # User management app
├── dormitory/       # Dormitory management app
├── student/         # Student profile management
├── payment/         # Payment integration
└── joybor/          # Project settings
```

## Environment Variables

See `.env.example` for all required environment variables.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 