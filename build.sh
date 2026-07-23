#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

# Force migrate all apps
python manage.py migrate --noinput

# Show status
python manage.py showmigrations

echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'vysal99999@gmail.com', 'Admin123@')" | python manage.py shell

echo "Admin seeding completed."

echo "Build completed."