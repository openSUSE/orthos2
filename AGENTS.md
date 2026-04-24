# AGENTS.md

This file provides guidance to AI Agents when working with code in this repository.

## Project Overview

Orthos2 is a Django-based machine administration tool used by SUSE's development network. It manages:
- Machine state and hardware inventory
- Software installations tracking
- Machine reservations
- DHCP configuration via Cobbler
- Remote reboots and serial console access
- Integration with Netbox for network management

## Architecture

### Django Apps Structure

The project is organized into specialized Django apps:

- **orthos2/data**: Core domain models and business logic
  - Models: `Machine`, `Domain`, `NetworkInterface`, `BMC`, `SerialConsole`, `RemotePower`, `Installation`, `ReservationHistory`, `Enclosure`, `MachineGroup`, etc.
  - Handles virtualization, server config management, and hardware components
  
- **orthos2/api**: REST API layer using Django REST Framework
  - Command-based architecture in `api/commands/` (`add.py`, `delete.py`, `info.py`, `power.py`, `query.py`, `reserve.py`, etc.)
  - Token authentication for CLI and programmatic access
  - Serializers in `api/serializers/`

- **orthos2/frontend**: Web interface
  - Django template-based views (not SPA)
  - Views organized by function in `frontend/views/` (`machine.py`, `machines.py`, `user.py`, `statistics.py`, etc.)
  - AJAX endpoints for dynamic updates

- **orthos2/taskmanager**: Asynchronous task processing
  - Runs as a separate service (see `compose.yaml`)
  - Task types in `taskmanager/tasks/`: `ansible.py`, `cobbler.py`, `netbox.py`, `machinetasks.py`, `sconsole.py`, `notifications.py`, etc.
  - Handles long-running operations like Cobbler regeneration, Netbox sync, machine scanning

- **orthos2/utils**: Shared utilities and helpers

- **cli/**: Command-line client (`orthos2` script)
  - Python-based CLI for interacting with the API
  - Uses configuration from `~/.config/orthosrc` or `/etc/orthosrc`

### Key External Integrations

- **Cobbler**: DHCP/PXE boot configuration generation
- **Netbox**: Network inventory synchronization
- **Authentik**: OpenID Connect authentication
- **Paramiko/SSH**: Remote machine access and management

### Database

- PostgreSQL in production/Docker (configured via `ORTHOS2_DB_ENGINE`, `ORTHOS2_POSTGRES_*` env vars)
- SQLite for local development (default)
- Settings: timezone is Europe/Berlin, uses custom date formats

## Development Commands

### Running the Development Environment

The primary development workflow uses Docker Compose:

```bash
# Start all services (Orthos2, PostgreSQL, Netbox, Cobbler, Authentik, Traefik)
docker compose up -d

# Access services at:
# - https://orthos2.orthos2.test (main app)
# - https://netbox.orthos2.test (Netbox)
# - https://authentik.orthos2.test (auth provider)
# - https://cobbler.orthos2.test (Cobbler)

# Note: Add to /etc/hosts:
# 127.0.0.1 authentik.orthos2.test orthos2.orthos2.test cobbler.orthos2.test netbox.orthos2.test
```

The compose setup includes:
- `orthos2`: Main Django application (port 8000)
- `orthos2_taskmanager`: Background task processor
- `orthos2_database`: PostgreSQL database
- `cobbler`, `netbox`, `authentik`: Integrated services
- `proxy`: Traefik reverse proxy

### Running Tests

```bash
# Run all tests
docker compose exec -it orthos2 pytest

# Run specific app tests
docker compose exec -it orthos2 pytest orthos2/data
docker compose exec -it orthos2 pytest orthos2/dataapi
docker compose exec -it orthos2 pytest orthos2/datafrontend

# Run specific test file
docker compose exec -it orthos2 pytest -k "test_serverconfig"
```

### Code Quality

```bash
# Format code with black
black .

# Sort imports
isort .

# Format templates with prettier
npx prettier --write "**/*.html"

# Run pre-commit hooks manually
pre-commit run --all-files

# Type checking (configured for Python 3.11, strict mode)
pyright
```

Pre-commit hooks automatically run `black` and `isort` on commit.

### Django Management

```bash
# Run development server (works only in the container and is automatically started)
docker/devel-server.sh

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load fixture data (useful for development)
python manage.py loaddata orthos2/data/fixtures/architectures.json
python manage.py loaddata orthos2/data/fixtures/platforms.json
python manage.py loaddata orthos2/data/fixtures/serialconsoletypes.json
python manage.py loaddata orthos2/data/fixtures/systems.json
```

### Container Development Workflow

For development inside a container:

```bash
# Build development image
docker compose build

# Run Docker Compose stack
docker compose up -d
```

## Configuration

- **Settings**: `orthos2/settings.py` (main), `/etc/orthos2/settings` (production override)
- **Environment variables**: All `ORTHOS_*` and `ORTHOS2_*` prefixed vars (see `docker/orthos/orthos2.env` for examples)
- **Key env vars**:
  - `ORTHOS_SECRET_KEY`: Django secret key
  - `ORTHOS2_DB_ENGINE`: Database backend
  - `ORTHOS2_POSTGRES_*`: PostgreSQL connection settings
  - `ALLOWED_HOSTS`: Django allowed hosts
  - `ORTHOS_NETBOX_URL`, `ORTHOS_NETBOX_TOKEN`: Netbox integration
  - `OIDC_KEY`, `OIDC_SECRET`: Authentication configuration

## Important Development Notes

### Taskmanager Service

The taskmanager runs as a **separate process** (`ORTHOS2_MODE=taskmanager`). When modifying tasks:
- Code changes require restarting the `orthos2_taskmanager` container
- Tasks communicate via database (task queue model)
- Check taskmanager logs separately from web app logs

### API Command Pattern

API endpoints follow a command pattern:
- Each command in `api/commands/` implements specific operations
- Commands validate input via forms in `api/forms.py`
- Serializers in `api/serializers/` handle data transformation
- URL routing in `api/urls.py` maps endpoints to command handlers

### Model Relationships

Key relationships to understand:
- `Machine` is the central model, related to `Domain`, `NetworkInterface`, `BMC`, `SerialConsole`, `Installation`
- `Machine` can be part of `MachineGroup` (many-to-many via `MachineGroupMembership`)
- `Machine` has `ReservationHistory` for tracking usage
- `Enclosure` contains multiple machines (physical chassis relationship)
- `RemotePowerDevice` controls power for multiple machines

### Testing

- Tests use Django's `TestCase` framework
- Test data fixtures in `*/fixtures/` directories
- Test files in `*/tests/` directories
- Some tests require database fixtures to be loaded first

### Static Files & Templates

- Frontend uses Django templates (not a JavaScript SPA)
- Static files in `frontend/static/`
- Templates in `frontend/templates/`
- Template formatting uses Prettier with django/jinja plugins

## Common Workflows

### Adding a New API Endpoint

1. Create command class in `orthos2/api/commands/` (inherit from base command)
2. Add form validation in `orthos2/api/forms.py` if needed
3. Create/update serializer in `orthos2/api/serializers/`
4. Add URL route in `orthos2/api/urls.py`
5. Add tests in `orthos2/api/tests/commands/`

### Adding a New Model

1. Create model file in `orthos2/data/models/` or add to existing file
2. Import and export in `orthos2/data/models/__init__.py`
3. Create migration: `python manage.py makemigrations`
4. Create serializer in `orthos2/api/serializers/`
5. Add admin interface in `orthos2/data/admin.py` if needed
6. Add tests in `orthos2/data/tests/`

### Adding a Background Task

1. Create task module in `orthos2/taskmanager/tasks/`
2. Import task in `orthos2/taskmanager/tasks/__init__.py`
3. Task will be executed by taskmanager service
4. Remember to restart `orthos2_taskmanager` container to load new tasks
