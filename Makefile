SHELL := /bin/bash
PROJECT ?= production
NO_CACHE ?=

DOCKER_BUILD := DOCKER_BUILDKIT=1 docker build $(if $(NO_CACHE),--no-cache,)

COMPOSE_DEV := docker compose -f compose.common.yaml -f compose.dev.yaml -f compose.dev.override.yml
COMPOSE_TESTING := docker compose -f compose.common.yaml -f compose.testing.yaml -f compose.dev.override.yml
COMPOSE_PROD := docker compose -f compose.yaml

.PHONY: help \
	build-dev up-dev down-dev logs-dev clean-dev test-dev \
	pull-testing build-testing up-testing down-testing logs-testing clean-testing \
	pull-prod up-prod down-prod logs-prod

help:
	@echo "Targets: build-dev up-dev down-dev logs-dev clean-dev | pull-testing build-testing up-testing down-testing logs-testing clean-testing | pull-prod up-prod down-prod logs-prod"
	@echo "Set NO_CACHE=1 to force --no-cache on any build-* target."
	@echo "Run pull-testing/pull-prod first to fetch OBS images rebuilt under the same tag before building/starting."

# --- dev stack (docker/develop.dockerfile) ---
build-dev:
	$(DOCKER_BUILD) -f docker/develop.dockerfile -t orthos2:dev-latest \
		--secret id=SCCcredentials,src=docker/secrets/SCCcredentials .
	$(DOCKER_BUILD) -f docker/nginx/nginx.dockerfile -t orthos2-static:dev-latest \
		--build-arg BASE_IMAGE=orthos2:dev-latest docker/nginx
	$(COMPOSE_DEV) build

up-dev: build-dev
	$(COMPOSE_DEV) up -d

down-dev:
	$(COMPOSE_DEV) down

logs-dev:
	$(COMPOSE_DEV) logs -f

clean-dev: down-dev
	docker image rm -f orthos2:dev-latest orthos2-static:dev-latest

test-dev:
	$(COMPOSE_DEV) exec -it orthos2 bash -c 'coverage run --source="." -m pytest orthos2'
	$(COMPOSE_DEV) exec -it orthos2 bash -c 'coverage report'
	$(COMPOSE_DEV) exec -it orthos2 bash -c 'coverage xml'

# --- testing stack (docker/production.dockerfile, exercised without a full prod env) ---
# OBS rebuilds these base images on transitive dependency changes without changing the
# tag, so `docker build` alone won't notice new content - pull explicitly to refresh them.
pull-testing:
	docker pull registry.suse.com/bci/bci-base:15.7
	docker pull registry.suse.com/suse/nginx:1.27

build-testing:
	$(DOCKER_BUILD) -f docker/production.dockerfile -t orthos2:latest \
		--secret id=SCCcredentials,src=docker/secrets/SCCcredentials \
		--build-arg PROJECT=$(PROJECT) docker
	$(DOCKER_BUILD) -f docker/nginx/nginx.dockerfile -t orthos2-static:latest \
		--build-arg BASE_IMAGE=orthos2:latest docker/nginx
	$(COMPOSE_TESTING) build

up-testing: build-testing
	$(COMPOSE_TESTING) up -d

down-testing:
	$(COMPOSE_TESTING) down

logs-testing:
	$(COMPOSE_TESTING) logs -f

clean-testing: down-testing
	docker image rm -f orthos2:latest orthos2-static:latest

# --- production stack (prebuilt registry images, nothing to build) ---
# OBS rebuilds these images on transitive dependency changes without changing the tag,
# so a local pull is needed to actually fetch the new content.
pull-prod:
	$(COMPOSE_PROD) pull

up-prod:
	$(COMPOSE_PROD) up -d

down-prod:
	$(COMPOSE_PROD) down

logs-prod:
	$(COMPOSE_PROD) logs -f
