#!/usr/bin/bash

server_start() {
    export DJANGO_SETTINGS_MODULE="orthos2.settings"
    if django-admin shell -c "from django.db import connection; connection.ensure_connection()"; then
        echo "Success!"
    else
        echo "Connection failed!" 1>&2
        exit 1
    fi
    ORTHOS2_SECRET_KEY=$(cat /run/secrets/OrthosKey)
    export ORTHOS2_SECRET_KEY
    ORTHOS2_NETBOX_TOKEN=$(cat /run/secrets/NetboxToken)
    export ORTHOS2_NETBOX_TOKEN
    OIDC_SECRET=$(cat /run/secrets/OIDCsecret)
    export OIDC_SECRET
    orthos-admin migrate
    /usr/bin/gunicorn -b 0.0.0.0:8000 orthos2.wsgi:application
}

taskmanager_start() {
    ORTHOS2_SECRET_KEY=$(cat /run/secrets/OrthosKey)
    export ORTHOS2_SECRET_KEY
    ORTHOS2_NETBOX_TOKEN=$(cat /run/secrets/NetboxToken)
    export ORTHOS2_NETBOX_TOKEN
    OIDC_SECRET=$(cat /run/secrets/OIDCsecret)
    export OIDC_SECRET
    # Wait for it
    until curl --output /dev/null --silent --head --fail http://orthos2:8000; do
        echo "Waiting for main application to become available"
        sleep 5
    done
    # Start server
    orthos-admin taskmanager --start
}

if [ "$ORTHOS2_MODE" == "taskmanager" ]; then
    taskmanager_start
else
    server_start
fi
