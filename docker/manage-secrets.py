#!/usr/bin/python3

"""
This script generates random secrets and passwords for various containers utilized during Orthos 2 testing.
"""

import pathlib
from typing import List

from django.core.management.utils import get_random_secret_key
from django.utils.crypto import get_random_string

DJANGO_REST_ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"
DJANGO_REST_TOKEN_LENGTH = 40

script_directory = pathlib.Path(__file__).resolve().parent

netbox_secret_key = get_random_secret_key()
orthos2_secret_key = get_random_secret_key()

redis_password = get_random_string(12)
redis_cache_password = get_random_string(12)
netbox_db_password = get_random_string(12)
netbox_superuser_api_token = get_random_string(
    DJANGO_REST_TOKEN_LENGTH, DJANGO_REST_ALLOWED_CHARS
)
netbox_superuser_password = get_random_string(12)
orthos_db_password = get_random_string(12)
orthos_superuser_password = get_random_string(12)

# netbox.env
# DB_PASSWORD, REDIS_CACHE_PASSWORD, REDIS_PASSWORD, SECRET_KEY, SUPERUSER_API_TOKEN, SUPERUSER_PASSWORD

netbox_env_file = script_directory / "netbox" / "netbox.env"
netbox_env_vars_str = netbox_env_file.read_text()
netbox_env_vars_old = netbox_env_vars_str.splitlines()
netbox_env_vars_new: List[str] = []
for line in netbox_env_vars_old:
    if line.startswith("DB_PASSWORD="):
        line = line.replace(line, f"DB_PASSWORD={netbox_db_password}")
    elif line.startswith("REDIS_CACHE_PASSWORD="):
        line = line.replace(line, f"REDIS_CACHE_PASSWORD={redis_cache_password}")
    elif line.startswith("REDIS_PASSWORD="):
        line = line.replace(line, f"REDIS_PASSWORD={redis_password}")
    elif line.startswith("SECRET_KEY="):
        line = line.replace(line, f"SECRET_KEY='{netbox_secret_key}'")
    elif line.startswith("SUPERUSER_API_TOKEN="):
        line = line.replace(line, f"SUPERUSER_API_TOKEN={netbox_superuser_api_token}")
    elif line.startswith("SUPERUSER_PASSWORD="):
        line = line.replace(line, f"SUPERUSER_PASSWORD={netbox_superuser_password}")
    netbox_env_vars_new.append(line)
netbox_env_file.write_text("\n".join(netbox_env_vars_new) + "\n")

# postgres.env
# POSTGRES_PASSWORD

(script_directory / "netbox" / "postgres.env").write_text(
    "POSTGRES_DB=netbox\n"
    f"POSTGRES_PASSWORD={netbox_db_password}\n"
    "POSTGRES_USER=netbox\n"
)

# redis.env
# REDIS_PASSWORD

(script_directory / "netbox" / "redis.env").write_text(
    f"REDIS_PASSWORD={redis_password}\n"
)

# redis-cache.env
# REDIS_PASSWORD

(script_directory / "netbox" / "redis-cache.env").write_text(
    f"REDIS_PASSWORD={redis_cache_password}\n"
)

# db.env
# ORTHOS2_POSTGRES_PASSWORD

(script_directory / "orthos" / "db.env").write_text(
    "POSTGRES_USER: orthos\n" f'POSTGRES_PASSWORD="{orthos_db_password}"\n'
)

# orthos2.env
# ORTHOS_SECRET_KEY, ORTHOS_NETBOX_TOKEN

(script_directory / "orthos" / "orthos2.env").write_text(
    f'ORTHOS_SECRET_KEY="{orthos2_secret_key}"\n'
    'ORTHOS_NETBOX_URL="http://netbox.orthos2.test:8080"\n'
    f"ORTHOS_NETBOX_TOKEN='{netbox_superuser_api_token}'\n"
    f'ORTHOS_SUPERUSER_PASSWORD="{orthos_superuser_password}"\n'
    'ORTHOS2_DB_ENGINE="django.db.backends.postgresql_psycopg2"\n'
    'ORTHOS2_POSTGRES_HOST="database.orthos2.test"\n'
    'ORTHOS2_POSTGRES_NAME="orthos"\n'
    'ORTHOS2_POSTGRES_USER="orthos"\n'
    f'ORTHOS2_POSTGRES_PASSWORD="{orthos_db_password}"\n'
)
