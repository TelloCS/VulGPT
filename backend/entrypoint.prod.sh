#!/bin/sh
set -e

echo "Gathering static files for Nginx..."
python manage.py collectstatic --noinput --clear

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting the application server..."

exec "$@"