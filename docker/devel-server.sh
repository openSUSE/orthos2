#!/usr/bin/bash


server_start() {
    git config --global --add safe.directory /code
    OLD_BRANCH=$(git branch --show-current)
    git stash -u
    git switch master
    python3 manage.py migrate
    if [ -f "dump.json" ]; then
        python3 manage.py flush --noinput
        python3 manage.py loaddata dump.json
    fi
    git switch "$OLD_BRANCH"
    git stash pop
    python3 manage.py migrate
    DJANGO_SUPERUSER_PASSWORD='admin' python3 manage.py createsuperuser --noinput --username admin --email admin@example.com
    python3 manage.py shell < /code/docker/django-generate-admin-token
    python3 manage.py runserver 0.0.0.0:8000
}

taskmanager_start() {
    # Wait for it
    until curl --output /dev/null --silent --head --fail http://orthos2.orthos2.test:8000; do
        echo "Waiting for main application to become available"
        sleep 5
    done
    # Moves files into place
    python3 manage.py setup ansible --buildroot="/"
    # Start server
    python3 manage.py taskmanager --start
}

if [ "$ORTHOS2_MODE" == "taskmanager" ]; then
    taskmanager_start
else
    server_start
fi
