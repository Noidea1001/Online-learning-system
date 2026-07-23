#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

# ដំណើរការបង្កើតតារាងក្នុង Database
python manage.py migrate --noinput

# បង្កើត Superuser ដោយស្វ័យប្រវត្តិតាមរយៈ Environment Variables ខាងលើ
python manage.py createsuperuser --noinput || echo "Superuser already exists or creation skipped."

# Show status
python manage.py showmigrations

echo "Build completed."
