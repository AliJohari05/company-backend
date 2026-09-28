# CtrlOps Staging Deployment

This guide deploys the Django API with PostgreSQL, Redis, Celery, Gunicorn,
and Caddy. Caddy obtains and renews HTTPS certificates automatically, so do
not add Nginx unless a separate infrastructure requirement specifically needs it.

## 1. Code quality checks

Run these checks from a development environment before building the staging
image:

```bash
pip install -r requirements-dev.txt
black --check .
isort --check-only .
ruff check .
```

## 2. Server requirements

- A Linux server with Docker Engine and Docker Compose v2
- A public DNS `A`/`AAAA` record for the staging API domain
- Inbound TCP ports `80` and `443`
- Outbound access to the selected SMTP provider

Do not expose PostgreSQL port `5432` publicly.

## 3. Create staging secrets

Copy the example without committing the resulting file:

```bash
cp .env.staging.example .env.staging
```

Generate a Django secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Replace every placeholder in `.env.staging`, particularly:

- `SECRET_KEY`
- `STAGING_DOMAIN`
- `ACME_EMAIL`
- `ALLOWED_HOSTS`
- `API_SERVER_URL`
- `FRONTEND_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- all SMTP values

Keep `CORS_ALLOW_ALL_ORIGINS=False` and `DEBUG=False`.

## 3. Validate configuration

```bash
docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  config --quiet
```

Build the application image:

```bash
docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  build
```

Run Django's production security check:

```bash
docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  run --rm --no-deps web python manage.py check --deploy
```

## 4. Start staging

```bash
docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  up -d
```

The one-shot `migrate` service runs these deployment tasks before the web,
worker, and beat services start:

1. `migrate --noinput`
2. `compilemessages`
3. `collectstatic --noinput`

Redis is not exposed on a host port: it is only reachable by the Docker
services. Celery Beat must remain a single replica; running multiple beat
instances can dispatch a periodic task more than once.

If the staging database/media were copied from an older deployment where
project or ticket attachments were public, migrate those files once:

```bash
docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  exec web python manage.py move_private_uploads --dry-run

docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  exec web python manage.py move_private_uploads
```

Inspect health and logs:

```bash
docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  ps

docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  logs -f web worker beat redis proxy
```

The readiness endpoint is:

```text
https://<STAGING_DOMAIN>/health/
```

## 5. Create the initial administrator

```bash
docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  exec web python manage.py createsuperuser
```

## 6. SMTP verification

Use a staging/test domain with SPF and DKIM configured by the email provider.
Set a real `DEFAULT_FROM_EMAIL` on that domain. Register a temporary user and
verify all of the following:

- the message arrives in inbox rather than spam;
- its frontend verification URL uses HTTPS and the staging frontend domain;
- Persian requests produce an RTL Persian email;
- verification activates the account;
- resend throttling returns HTTP `429` after the configured limit.

Do not use the console email backend on staging.

## 7. API documentation

`API_DOCS_ENABLED=True` exposes Swagger and ReDoc on staging. Set it to
`False` if documentation should not be public. If it remains enabled, protect
the staging domain with an external access policy or HTTP authentication.

## 8. Backups

Create a database and upload backup:

```bash
sh deploy/backup.sh .env.staging ./backups
```

The command creates:

- `database.sql`
- `uploads.tar.gz` containing public and private uploads
- `SHA256SUMS`

Copy backups to storage outside the staging server. A backup is not considered
valid until a restore has been tested on a separate database/server.

Recommended minimum retention:

- daily backups for 7 days;
- weekly backups for 4 weeks;
- one monthly backup for 3 months.

## 9. Updating staging

Take a backup first, then:

```bash
git pull --ff-only

docker compose \
  --env-file .env.staging \
  -f docker-compose.staging.yml \
  up -d --build
```

After every update, verify `/health/`, Swagger schema generation, login,
email verification, password-reset delivery, private downloads, and one
database write operation. Confirm `worker` and `beat` are running with
`docker compose ... ps`; the daily billing-status task runs at 00:05 UTC.
