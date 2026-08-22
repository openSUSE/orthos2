#!/usr/bin/bash

get_netbox_token() {
    # Docker takes care of starting NetBox before the Orthos 2 container is started. As such this API endpoint can be
    # reliably called.
    NETBOX_TOKEN_JSON=$(curl -s -X POST \
      -H "Content-Type: application/json" \
      -H "Accept: Application/json; indent=4" \
      "${ORTHOS2_NETBOX_URL}/api/users/tokens/provision/" \
      --data "{\"username\": \"${NETBOX_SUPERUSER_NAME}\", \"password\": \"${NETBOX_SUPERUSER_PASSWORD}\"}")
    ORTHOS2_NETBOX_TOKEN="nbt_$(echo "$NETBOX_TOKEN_JSON" | jq -r '.key').$(echo "$NETBOX_TOKEN_JSON" | jq -r '.token')"
    echo "$ORTHOS2_NETBOX_TOKEN"
}

server_start() {
    # Setup NetBox
    ORTHOS2_NETBOX_TOKEN=$(get_netbox_token)
    export ORTHOS2_NETBOX_TOKEN
    python3.11 manage.py shell </code/docker/orthos/setup_netbox.py
    # Setup Orthos 2
    git config --global --add safe.directory /code
    OLD_BRANCH=$(git branch --show-current)
    git stash -u
    git switch master
    python3.11 manage.py migrate
    if [ -f "dump.json" ]; then
        python3.11 manage.py flush --noinput
        python3.11 manage.py loaddata dump.json
    fi
    git switch "$OLD_BRANCH"
    git stash pop
    python3.11 manage.py migrate
    # Load test machine fixtures for development. Both fixtures use fixed
    # keys/fqdns that collide with a previous run's data on the persistent dev
    # DB, so skip loading them again if that data is already there.
    python3.11 manage.py shell -c "
from orthos2.data.models import ServerConfig
exit(0 if ServerConfig.objects.filter(key='domain.validendings').exists() else 1)
" || python3.11 manage.py loaddata orthos2/data/fixtures/tests/test_domain_orthos2test.json
    python3.11 manage.py shell -c "
from orthos2.data.models import Machine
exit(0 if Machine.objects.filter(fqdn='testmachine.orthos2.test').exists() else 1)
" || python3.11 manage.py loaddata orthos2/data/fixtures/tests/test_machine_docker.json
    python3.11 manage.py shell -c "
from django.contrib.auth.models import User
exit(0 if User.objects.filter(username='admin').exists() else 1)
" || DJANGO_SUPERUSER_PASSWORD="$ORTHOS2_SUPERUSER_PASSWORD" python3.11 manage.py createsuperuser --noinput --username admin --email admin@example.com
    python3.11 manage.py shell </code/docker/orthos/django-generate-admin-token
    python3.11 manage.py runserver 0.0.0.0:8000
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
    ORTHOS2_NETBOX_TOKEN=$(get_netbox_token)
    export ORTHOS2_NETBOX_TOKEN
    # Moves files into place
    python3.11 manage.py setup ansible --buildroot="/"
    # Start server
    python3.11 manage.py taskmanager --start
}

if [ "$ORTHOS2_MODE" == "taskmanager" ]; then
    taskmanager_start
else
    server_start
fi
