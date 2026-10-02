# Local monitoring stack (optional)

A minimal Prometheus + Grafana + Blackbox Exporter stack for exercising the
`ORTHOS2_PROMETHEUS_URL`/`ORTHOS2_GRAFANA_URL` integration locally, without needing the real
mgmt_cluster stack. It's an **optional add-on** on top of the dev stack (see `compose.monitoring.yml`
at the repo root) - it is not started by `make up-dev`.

## What's in here

- `prometheus.yml` - scrape config for `icmp-arch-ipv4`/`icmp-arch-ipv6`/`ssh-arch`, matching the
  job names `orthos2/settings.py` defaults to. Targets are discovered dynamically via the
  `cobbler_http_sd` service (same as production), so this stays useful even as the local dev
  Cobbler's registered systems change.
- `blackbox.yml` - the same `icmpv4`/`icmpv6`/`ssh_banner` module definitions used in production
  (`orthos2-gitops`'s `03-blackbox-exporter-release.yml`).
- `grafana/provisioning/datasources/datasource.yml` - auto-provisions Prometheus as Grafana's
  default datasource, with `uid: prometheus-orthos2` to match the dashboards below.
- `grafana/dashboards/*.json` - the same three dashboards built for the real mgmt_cluster stack,
  copied verbatim from `orthos2-gitops`'s `01-configmap-orthos2-dashboards.yml` (Admin
  Infrastructure Overview, Host Overview, and Host Details - the one
  `GRAFANA_HOST_DASHBOARD_UID` links to from the machine detail page). Auto-provisioned via
  `grafana/provisioning/dashboards/dashboards.yaml`; work unmodified since the datasource uid
  matches. If you update the dashboards in orthos2-gitops, re-copy them here to keep both in sync
  (there's no automation tying the two together).

## Usage

```sh
make up-dev-monitoring   # starts the dev stack plus prometheus/grafana/blackbox_exporter
```

This also sets `ORTHOS2_PROMETHEUS_URL=http://prometheus:9090` (internal, used server-side by the
Django app) and `ORTHOS2_GRAFANA_URL=https://grafana.orthos2.test` (used for browser-facing
dashboard links) on the `orthos2`/`orthos2_taskmanager` services, so `rescan <fqdn> status` and the
machine list/detail pages start reading real (if likely empty, since the local dev Cobbler
normally has no registered systems) data immediately.

Both UIs are exposed via Traefik, like the rest of the dev stack — add this to `/etc/hosts`
alongside the existing `orthos2.test` entries (AGENTS.md's base list doesn't include these two,
since this add-on is optional):

```
127.0.0.1 grafana.orthos2.test prometheus.orthos2.test
```

- Prometheus UI: https://prometheus.orthos2.test
- Grafana UI: https://grafana.orthos2.test (default login `admin`/`admin`, anonymous Viewer access
  is also enabled for convenience)

`make down-dev-monitoring`/`make logs-dev-monitoring` work the same way as the other `*-dev`
targets, just with this add-on included.
