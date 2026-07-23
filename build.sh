#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput

echo "=== Making migrations for all apps ==="
python manage.py makemigrations category lessons assignments submissions reviews enrollments employees courses students instructors users dashboard adminpanel quizzes notifications --noinput

echo "=== Applying all migrations ==="
python manage.py migrate --noinput

echo "=== Migration Status ==="
python manage.py showmigrations