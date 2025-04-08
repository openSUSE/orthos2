#!/usr/bin/bash

git config --global --add safe.directory /code
OLD_BRANCH=$(git branch --show-current)
git stash -u
git switch master
python3 manage.py migrate
if [ -f "dump.json" ]; then
    python3 manage.py loaddata dump.json
fi
git switch "$OLD_BRANCH"
git stash pop
python3 manage.py migrate
DJANGO_SUPERUSER_PASSWORD='admin' python3 manage.py createsuperuser --noinput --username admin --email admin@example.com
python3 manage.py shell < /code/docker/django-generate-admin-token
python3 manage.py runserver 0.0.0.0:8000
