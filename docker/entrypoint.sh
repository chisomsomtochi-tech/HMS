#!/bin/sh
# Container entrypoint: prepare the database and static files, then start the
# command passed as CMD (Gunicorn by default).
set -eu

if [ -z "${DJANGO_SECRET_KEY:-}" ]; then
    echo "error: DJANGO_SECRET_KEY is not set. Add it to .env or the container environment." >&2
    exit 1
fi

# Keep SQLite on the mounted volume so data survives container replacement.
DJANGO_DB_PATH="${DJANGO_DB_PATH:-/app/data/db.sqlite3}"
export DJANGO_DB_PATH
mkdir -p "$(dirname "$DJANGO_DB_PATH")"

echo "Applying database migrations..."
python manage.py migrate --noinput

case "${RUN_SEED_DEMO:-False}" in
    1|true|True|TRUE)
        echo "Seeding demo clinic data..."
        python manage.py seed_demo
        ;;
esac

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
