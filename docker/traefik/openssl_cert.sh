#!/bin/bash

openssl req -x509 \
  -newkey rsa:2048 \
  -nodes \
  -keyout docker/traefik/certs/authentik.orthos2.test.key \
  -out docker/traefik/certs/authentik.orthos2.test.crt \
  -days 365 \
  -subj "/CN=authentik.orthos2.test" \
  -addext "subjectAltName=DNS:authentik.orthos2.test"
