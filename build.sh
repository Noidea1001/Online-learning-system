#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "=== Running all migrations ==="
python manage.py migrate --noinput

echo "=== Checking migration status ==="
python manage.py showmigrations

echo "Build completed."