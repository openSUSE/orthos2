# cobbler-http-sd

A Prometheus [HTTP service discovery](https://prometheus.io/docs/prometheus/latest/http_sd/)
adapter for Cobbler. Replaces the old `configgen.py` one-off script (in `orthos2-gitops`) that
wrote a static target list into git by hand. This service queries the configured Cobbler
servers' `get_systems()` XML-RPC call on demand (cached for `CACHE_TTL_SECONDS`) and serves the
current set of targets - both the `default` (host) and `bmc` interface of every system - as
Prometheus HTTP SD groups on `GET /sd`.

It is plain, dependency-free Python 3 (stdlib only: `http.server`, `xmlrpc.client`, `json`,
`threading`) so it has no dependency on Django, Orthos2, or a running Cobbler instance to be
*tested* - only to run for real.

## Configuration

| Env var | Default | Description |
|---|---|---|
| `COBBLER_SERVERS_CONFIG_PATH` | `/etc/cobbler-http-sd/servers.json` | Path to the server list (see below). |
| `CACHE_TTL_SECONDS` | `300` | How long a built target list is served before Cobbler is queried again. |
| `LISTEN_PORT` | `8080` | HTTP listen port. |

`servers.json` is a JSON array; each entry needs a `url` (the Cobbler XML-RPC endpoint) and may
optionally carry `username`/`password` for servers that require authentication:

```json
[
  {"url": "http://cobbler.example.org/cobbler_api"},
  {"url": "http://cobbler2.example.org/cobbler_api", "username": "changeme", "password": "changeme"}
]
```

Entries without `username`/`password` are queried anonymously.

## Endpoints

- `GET /sd` - the current Prometheus HTTP SD JSON array.
- `GET /healthz` - liveness/readiness probe target.

## Running the tests

This suite has its own `pytest.ini` (deliberately separate from the repo root's
`pyproject.toml`, which configures `pytest-django` for the main Orthos2 app) so it never
requires Django to be installed:

```sh
python3 -m pytest docker/cobbler-http-sd/tests/
```
