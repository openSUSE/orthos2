#!/usr/bin/bash

python3 manage.py migrate
DJANGO_SUPERUSER_PASSWORD='admin' python3 manage.py createsuperuser --noinput --username admin --email admin@example.com
python3 manage.py shell < /code/docker/django-generate-admin-token
python3 manage.py runserver 0.0.0.0:8000
