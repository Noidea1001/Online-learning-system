#!/usr/bin/env bash
set -o errexit

echo "Installing packages..."
pip install -r requirements.txt

echo "Collecting static..."
python manage.py collectstatic --noinput

echo "Making migrations..."
python manage.py makemigrations --noinput

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Migration status:"
python manage.py showmigrations

echo "Build done."