# Company Backend

Django REST backend for the company website and client portal. It provides public content, accounts, contact messages, projects, contracts, invoices, payments, tickets, and notifications.

## Stack

- Django and Django REST Framework
- PostgreSQL
- Redis and Celery for background email and scheduled maintenance
- Caddy as the production reverse proxy, TLS terminator, and static/media file server
- Docker Compose

## Services

```text
Browser / React frontend
          |
        Caddy
          |
       Django API ---- PostgreSQL
          |
        Redis
       /     \
Celery worker  Celery Beat
```

The Compose configuration starts a worker for asynchronous emails and a single Beat scheduler. Beat refreshes expired invoices and contracts daily at 00:05 UTC.

## Local development

1. Copy `.env.example` to `.env` and set the required values.
2. Start the application:

```bash
docker compose up --build
```

The API is available on `http://localhost:8000`. In development, API documentation is also enabled at `/api/docs/`.

Useful commands:

```bash
docker compose logs -f web
docker compose logs -f worker
docker compose logs -f beat
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test
```

## Configuration

Never commit `.env` files or production secrets. At a minimum, configure:

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS`
- PostgreSQL credentials (`DB_*`)
- Redis credentials (`REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`)
- SMTP credentials for verification and password-reset emails
- `CELERY_WORKER_CONCURRENCY` appropriate to the server CPU and available memory

Redis and PostgreSQL are intentionally internal Docker services in the staging deployment and must not be exposed directly to the public internet.

## Deployment

Use `.env.staging.example` as the template for a deployment environment, set `STAGING_DOMAIN` and `ACME_EMAIL`, then validate and start the stack:

```bash
STAGING_ENV_FILE=.env.staging docker compose --env-file .env.staging -f docker-compose.staging.yml config --quiet
STAGING_ENV_FILE=.env.staging docker compose --env-file .env.staging -f docker-compose.staging.yml up -d --build
```

Caddy obtains and renews HTTPS certificates automatically. Do not run Nginx alongside Caddy on ports 80 and 443. The detailed operational checklist is in [STAGING_DEPLOYMENT.md](STAGING_DEPLOYMENT.md).

Before each release, apply migrations through the included one-shot `migrate` service, verify worker and Beat logs, and back up the PostgreSQL volume/database.

## Background jobs

- Verification and password-reset emails are queued after the related database transaction commits.
- Celery retries transient SMTP/network failures.
- The scheduled billing job changes invoices past their due date and contracts past their end date to their expired state.

For local synchronous task execution in tests, set `CELERY_TASK_ALWAYS_EAGER=True`.

## Quality checks

Run these before deploying:

```bash
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py check --deploy
docker compose --env-file .env.staging -f docker-compose.staging.yml config --quiet
```

`check --deploy` may report HSTS preload as optional. Enable preload only after confirming that every present and future subdomain will be served exclusively over HTTPS.
