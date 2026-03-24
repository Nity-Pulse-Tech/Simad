#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "📡 Waiting for the database to be ready..."
sleep 5

if [ "$RUN_MIGRATIONS" = "1" ]; then
    echo "🛠️ Running migrations..."
    uv run python manage.py migrate --noinput
fi

if [ "$COLLECT_STATIC" = "1" ]; then
    echo "📦 Collecting static files..."
    uv run python manage.py collectstatic --noinput --clear
fi

if [ "$COMPILE_MESSAGES" = "1" ]; then
    echo "🌐 Compiling translations..."
    uv run python manage.py compilemessages -i .venv -i node_modules -l en # English
fi

echo "✅ Translation Compilation Complete"

# 🚀 Execute the container command (gunicorn, celery, etc.)
echo "🚀 Starting: $@"
exec "$@"