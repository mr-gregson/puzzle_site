#!/usr/bin/env bash

# Apply idempotent schema upgrades, then start the production WSGI server.
set -Eeuo pipefail

MODE="${1:-web}"
APP_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_ROOT"

# Allow host deployments to use a shell-compatible .env file. Container and
# orchestration deployments should inject secrets as environment variables.
ENV_FILE="${ENV_FILE:-$APP_ROOT/.env}"
if [[ -r "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

export FLASK_ENV="${FLASK_ENV:-production}"

: "${SECRET_KEY:?Set SECRET_KEY in the server environment or .env file}"
: "${DATABASE_URL:?Set DATABASE_URL in the server environment or .env file}"

if [[ ${#SECRET_KEY} -lt 32 || "$SECRET_KEY" == *"your-very-secure"* || "$SECRET_KEY" == *"change-this"* ]]; then
    echo "ERROR: SECRET_KEY must be a strong, non-placeholder value (at least 32 characters)." >&2
    exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
    if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
        PYTHON_BIN="$VIRTUAL_ENV/bin/python"
    elif [[ -x "$APP_ROOT/venv/bin/python" ]]; then
        PYTHON_BIN="$APP_ROOT/venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python3)"
    else
        echo "ERROR: Python 3 was not found. Install dependencies before startup." >&2
        exit 1
    fi
fi

"$PYTHON_BIN" -c 'import flask, gunicorn, sqlalchemy' || {
    echo "ERROR: Application dependencies are missing; install requirements.txt during deployment." >&2
    exit 1
}

mkdir -p "$APP_ROOT/logs"

case "$MODE" in
    migrate)
        echo "Applying database migrations..."
        exec "$PYTHON_BIN" "$APP_ROOT/migrations.py"
        ;;
    web)
        if [[ "${MIGRATE_ON_START:-true}" == "true" ]]; then
            echo "Applying database migrations..."
            "$PYTHON_BIN" "$APP_ROOT/migrations.py"
        else
            echo "Skipping startup migrations (MIGRATE_ON_START=false)."
        fi
        echo "Starting Puzzle Site on port ${PORT:-8000}..."
        exec "$PYTHON_BIN" -m gunicorn --config "$APP_ROOT/gunicorn.conf.py" wsgi:app
        ;;
    scheduler)
        echo "Starting the single-instance notification scheduler..."
        exec "$PYTHON_BIN" "$APP_ROOT/scheduler_worker.py"
        ;;
    *)
        echo "Usage: $0 [web|migrate|scheduler]" >&2
        exit 2
        ;;
esac