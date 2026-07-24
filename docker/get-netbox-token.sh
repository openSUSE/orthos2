#!/usr/bin/env bash
#
# Provisions a fresh NetBox API token (via NetBox's user/pass token-provision endpoint,
# same as get_netbox_token() in devel-server.sh) and writes it to docker/secrets/NetboxToken
# so compose.testing.yaml / compose.yaml can mount it as the "NetboxToken" Docker secret.
#
# NetBox's own database has no persistent volume, so a token written on a previous run can
# go stale after a `down`/`up` cycle - this always (re)provisions rather than trying to
# detect staleness.
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="docker/orthos/orthos2dev.env"
TOKEN_FILE="docker/secrets/NetboxToken"
# Must match the file set used by `up-testing` (COMPOSE_TESTING in the Makefile): compose
# validates the whole merged project even when only targeting "netbox", and compose.common.yaml
# alone leaves orthos2/orthos2_taskmanager/orthos2_nginx without an image or build context.
COMPOSE_NETBOX="docker compose -f compose.common.yaml -f compose.testing.yaml -f compose.dev.override.yml"

if ! command -v jq >/dev/null; then
    echo "jq is required to parse NetBox's token response - please install it." >&2
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Missing $ENV_FILE - run 'python3 docker/manage-secrets.py' first." >&2
    exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

echo "Starting NetBox so a token can be provisioned..."
$COMPOSE_NETBOX up -d --wait netbox

echo "Provisioning NetBox API token..."
NETBOX_TOKEN_JSON=$($COMPOSE_NETBOX exec -T netbox curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Accept: Application/json; indent=4" \
    "http://localhost:8080/api/users/tokens/provision/" \
    --data "{\"username\": \"${NETBOX_SUPERUSER_NAME}\", \"password\": \"${NETBOX_SUPERUSER_PASSWORD}\"}")

KEY=$(echo "$NETBOX_TOKEN_JSON" | jq -r '.key')
TOKEN=$(echo "$NETBOX_TOKEN_JSON" | jq -r '.token')

if [ -z "$KEY" ] || [ "$KEY" = "null" ] || [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "Failed to provision NetBox token, got: $NETBOX_TOKEN_JSON" >&2
    exit 1
fi

echo "nbt_${KEY}.${TOKEN}" > "$TOKEN_FILE"
echo "NetBox token written to $TOKEN_FILE"
