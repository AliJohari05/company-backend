#!/bin/sh
set -eu

ENV_FILE="${1:-.env.staging}"
BACKUP_ROOT="${2:-./backups}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.staging.yml}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Environment file not found: $ENV_FILE" >&2
    exit 1
fi

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DESTINATION="${BACKUP_ROOT%/}/$TIMESTAMP"
mkdir -p "$DESTINATION"

export STAGING_ENV_FILE="$ENV_FILE"

docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    exec -T db \
    sh -c 'pg_dump --clean --if-exists --no-owner --no-privileges -U "$POSTGRES_USER" "$POSTGRES_DB"' \
    > "$DESTINATION/database.sql"

docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    exec -T web \
    tar -czf - -C /app media private_media \
    > "$DESTINATION/uploads.tar.gz"

sha256sum \
    "$DESTINATION/database.sql" \
    "$DESTINATION/uploads.tar.gz" \
    > "$DESTINATION/SHA256SUMS"

echo "Backup created at: $DESTINATION"
