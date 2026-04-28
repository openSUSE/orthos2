#!/usr/bin/bash

get_netbox_token() {
    # Docker takes care of starting NetBox before the Orthos 2 container is started. As such this API endpoint can be
    # reliably called.
    NETBOX_TOKEN_JSON=$(curl -s -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: Application/json; indent=4" \
      "${ORTHOS_NETBOX_URL}/api/users/tokens/provision/" \
      --data "{\"username\": \"${NETBOX_SUPERUSER_NAME}\", \"password\": \"${NETBOX_SUPERUSER_PASSWORD}\"}")
    ORTHOS_NETBOX_TOKEN="nbt_$(echo $NETBOX_TOKEN_JSON | jq -r '.key').$(echo $NETBOX_TOKEN_JSON | jq -r '.token')"
    export ORTHOS_NETBOX_TOKEN
}

server_start() {
    # Setup NetBox
    get_netbox_token
    python3 manage.py shell </code/docker/setup_netbox.py
    # Setup Orthos 2
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
    # Load test machine fixtures for development
    python3 manage.py loaddata orthos2/data/fixtures/tests/test_domain_orthos2test.json || true
    python3 manage.py loaddata orthos2/data/fixtures/tests/test_machine_docker.json || true
    DJANGO_SUPERUSER_PASSWORD="$ORTHOS_SUPERUSER_PASSWORD" python3 manage.py createsuperuser --noinput --username admin --email admin@example.com
    python3 manage.py shell </code/docker/django-generate-admin-token
    python3 manage.py runserver 0.0.0.0:8000
}

taskmanager_start() {
    # Wait for it
    until curl --output /dev/null --silent --head --fail http://orthos2.orthos2.test:8000; do
        echo "Waiting for main application to become available"
        sleep 5
    done
    # Expand via PYTHONPATH so the settings are found
    PYTHONPATH=/code
    export PYTHONPATH
    # Generate NetBox API Token
    get_netbox_token
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
