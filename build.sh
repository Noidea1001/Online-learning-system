#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

# Force migrate all apps
python manage.py migrate --noinput

# Show status
python manage.py showmigrations

echo "Build completed."