#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "📡 Waiting for the database to be ready..."
sleep 5

echo "🛠️ Running migrations..."
uv run python manage.py migrate --noinput

echo "📦 Collecting static files..."
uv run python manage.py collectstatic --noinput --clear

echo "🌐 Compiling translations..."
uv run python manage.py compilemessages -i .venv -i node_modules -l en # English

echo "✅ Translation Compilation Complete"

# 🚀 Execute the container command (gunicorn, celery, etc.)
echo "🚀 Starting: $@"
exec "$@"