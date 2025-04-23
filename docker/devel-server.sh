#!/usr/bin/bash

setup_netbox() {
    # Create Custom Field Choice Set
    curl -X POST \
      -H "Authorization: Token efa8c297936bd152cde34326e26d6b866de03fad" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json; indent=4" \
      http://netbox.orthos2.test:8080/api/extras/custom-field-choice-sets/ \
      --data '{
        "name": "arch choices",
        "extra_choices": [["aarch64", "aarch64"], ["i386", "i386"], ["ia64", "ia64"], ["ppc64", "ppc64"], ["ppc64le", "ppc64le"], ["riscv64", "riscv64"], ["s390x", "s390x"], ["x86_64", "x86_64"]],
        "order_alphabetically": true
      }'
    # Create Custom Field "arch"
    curl -X POST \
      -H "Authorization: Token efa8c297936bd152cde34326e26d6b866de03fad" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json; indent=4" \
      http://netbox.orthos2.test:8080/api/extras/custom-fields/ \
      --data '{
        "name": "arch",
        "label": "CPU Architecture",
        "object_types": ["dcim.device", "virtualization.virtualmachine"],
        "type": "select",
        "choice_set": { "name": "arch choices" }
      }'
    # Create Custom Field "product_code"
    curl -X POST \
      -H "Authorization: Token efa8c297936bd152cde34326e26d6b866de03fad" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json; indent=4" \
      http://netbox.orthos2.test:8080/api/extras/custom-fields/ \
      --data '{
        "name": "product_code",
        "label": "Product Code",
        "object_types": ["dcim.device"],
        "type": "text"
      }'
    # Create Site Group
    # Create Site
    # Create Region
    # Create Location
    # Create Rack
    # Create Role
    # Create Platform
    # Create Prefix
    # Create IP Address - With DNS Name
    # Create Device Types (normal Server, PPC, S390X, aarch64)
    # Create Device - Standalone
    # Create Interface - With MAC and IP (v4 & v6)
    # Create Interface - With MAC and IP (v4)
    # Create Interface - With MAC and IP (v6)
    # Create Interface - With MAC
    # Create Interface - Empty
    # Create Interface - Mgmt
    # Mark IP Address as Primary for Device and Mgmt
    # Create Device - For Cluster
    # Create Cluster (single device)
    # Create Devices [1-3] - For Cluster
    # Create Multi-Device Cluster
    # Create 3 VMs for each Cluster
}

server_start() {
    # Setup NetBox
    setup_netbox
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
