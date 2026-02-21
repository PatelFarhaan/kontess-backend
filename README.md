# Kontess Backend

A Django REST Framework backend for **Kontess**, a hackathon and contest management platform. It provides comprehensive APIs for managing events, teams, participants, judges, tasks, grading, announcements, and notifications, with JWT-based authentication.

## Tech Stack

- **Language:** Python 3.8+
- **Framework:** Django 2.1 + Django REST Framework
- **Database:** PostgreSQL
- **Authentication:** JWT (via Simple JWT)
- **API Docs:** Swagger (django-rest-swagger)
- **Task Scheduling:** Django management commands for email notifications

## Features

- **User Management:** Registration, authentication, profile management with role-based access (Admin, Participant, Judge, Organizer)
- **Event Management:** Create and manage hackathon events with event logging
- **Team Management:** Team creation, invitations, member management, track assignment
- **Task System:** Task creation, assignment, submission tracking, and grading
- **Judge System:** Judge requests, mentor requests, and grading workflows
- **Announcements & Notifications:** Event-wide announcements and user notifications
- **Email Notifications:** Automated emails for task deadlines and grading reminders
- **Swagger API Documentation:** Interactive API docs at `/swagger-ui/`

## Prerequisites

- Python 3.8+
- PostgreSQL
- pip

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/kon_backend.git
   cd kon_backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Create the database:**
   ```bash
   createdb kontess
   ```

6. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

## Environment Variables

| Variable              | Description                          | Default                          |
|-----------------------|--------------------------------------|----------------------------------|
| `DJANGO_SECRET_KEY`   | Django secret key                    | `change-me-in-production`        |
| `DEBUG`               | Enable debug mode                    | `True`                           |
| `ALLOWED_HOSTS`       | Comma-separated allowed hosts        | `*`                              |
| `DB_NAME`             | PostgreSQL database name             | `kontess`                        |
| `DB_USER`             | PostgreSQL user                      | `postgres`                       |
| `DB_PASSWORD`         | PostgreSQL password                  | (empty)                          |
| `DB_HOST`             | PostgreSQL host                      | `localhost`                      |
| `DB_PORT`             | PostgreSQL port                      | `5432`                           |
| `EMAIL_BACKEND`       | Django email backend                 | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST`          | SMTP host                            | `smtp.gmail.com`                 |
| `EMAIL_HOST_USER`     | SMTP username                        | (empty)                          |
| `EMAIL_HOST_PASSWORD` | SMTP password                        | (empty)                          |
| `EMAIL_PORT`          | SMTP port                            | `587`                            |
| `FRONTEND_BASE_URL`   | Frontend URL for email links         | `http://localhost:3000`          |
| `CORS_ORIGIN_WHITELIST` | Comma-separated CORS origins       | `http://localhost`               |

## How to Run

```bash
make install
make migrate
make run
```
The API will be available at `http://localhost:8000`.

## API Endpoints

| Endpoint                       | Description                          |
|--------------------------------|--------------------------------------|
| `POST /api/token/`             | Obtain JWT token pair                |
| `POST /api/token/refresh/`     | Refresh JWT access token             |
| `GET/POST /api/user/`          | User management                      |
| `GET/POST /api/participant/`   | Participant management               |
| `GET/POST /api/team/`          | Team management                      |
| `GET/POST /api/judge/`         | Judge management                     |
| `GET/POST /api/organizer/`     | Organizer management                 |
| `GET/POST /api/event/`         | Event management                     |
| `GET/POST /api/task/`          | Task management                      |
| `GET/POST /api/grading/`       | Task grading                         |
| `GET/POST /api/announcement/`  | Announcements                        |
| `GET/POST /api/notification/`  | Notifications                        |
| `GET /api/my-event/`           | User's events                        |
| `GET /swagger-ui/`             | Swagger API documentation            |
| `GET /admin/`                  | Django admin panel                   |

## Project Structure

```
kon_backend/
├── app/
│   ├── admins/             # Django admin configurations
│   ├── backends/           # Auth backends, middleware, filters, pagination
│   ├── management/         # Custom management commands (email tasks)
│   ├── models/             # Database models (User, Team, Event, Task, etc.)
│   ├── serializers/        # DRF serializers
│   ├── templates/          # Email HTML templates
│   └── views/              # API viewsets
├── root/
│   ├── settings.py         # Django settings
│   ├── prodsettings.py     # Production settings
│   ├── urls.py             # URL routing
│   └── wsgi.py             # WSGI configuration
├── latest/                 # Latest version of the app
├── manage.py               # Django management entry point
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image definition
└── Makefile                # Common development commands
```

## Related Repositories

- **Frontend:** [kon_frontend](https://github.com/<your-username>/kon_frontend) - React-based UI for the Kontess platform

## License

This project is licensed under the MIT License.
