#!/usr/bin/python3
"""
Prometheus HTTP service discovery (https://prometheus.io/docs/prometheus/latest/http_sd/)
adapter for Cobbler. Replaces the old one-off `configgen.py` script (which wrote a static
target list into git) with a long-running service that queries the configured Cobbler
servers' `get_systems()` XML-RPC on demand (short-TTL cached) and returns the current set of
targets - both the `default` (host) and `bmc` interface of every system - as valid Prometheus
HTTP SD groups.
"""

import json
import logging
import os
import threading
import time
import xmlrpc.client  # nosec: B411
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cobbler-http-sd")

CONFIG_PATH = os.environ.get(
    "COBBLER_SERVERS_CONFIG_PATH", "/etc/cobbler-http-sd/servers.json"
)
CACHE_TTL_SECONDS = float(os.environ.get("CACHE_TTL_SECONDS", "300"))
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "8080"))

KNOWN_INTERFACE_ROLES = ("default", "bmc")


def load_server_config(path: str) -> List[Dict[str, str]]:
    """
    Load the list of Cobbler servers to query. Each entry is `{"url": "..."}` with optional
    `"username"`/`"password"` for servers that require authentication.
    """
    with open(path, "r", encoding="UTF-8") as f:
        servers = json.load(f)
    if not isinstance(servers, list):
        raise ValueError("servers.json must contain a JSON array")
    return servers


def fetch_systems(server: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Fetch `get_systems()` from a single Cobbler server, logging in first if credentials are
    configured for it. Raises on failure - callers are expected to catch and skip the server.
    """
    url = server["url"]
    proxy = xmlrpc.client.ServerProxy(url)

    username = server.get("username")
    password = server.get("password")
    if username and password:
        try:
            proxy.login(username, password)
        except (xmlrpc.client.Fault, OSError) as e:
            logger.warning("Login to Cobbler server %s failed: %s", url, e)

    systems = proxy.get_systems()
    if not isinstance(systems, list):
        raise ValueError(
            f"Cobbler server {url} did not return a list for get_systems()"
        )
    return systems


def build_sd_groups(servers: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Query every configured Cobbler server and turn the result into Prometheus HTTP SD groups,
    one per system interface (`default`/`bmc`). A server that fails is logged and skipped
    rather than failing the whole response.
    """
    groups: List[Dict[str, Any]] = []

    for server in servers:
        url = server["url"]
        try:
            systems = fetch_systems(server)
        except (xmlrpc.client.Fault, OSError, ValueError) as e:
            logger.warning("Skipping Cobbler server %s: %s", url, e)
            continue

        for system in systems:
            interfaces = system.get("interfaces", {})
            for interface_name, interface in interfaces.items():
                if interface_name not in KNOWN_INTERFACE_ROLES:
                    continue

                dns_name = interface.get("dns_name")
                if not dns_name:
                    continue

                has_ipv4 = bool(interface.get("ip_address"))
                has_ipv6 = bool(interface.get("ipv6_address"))
                if not has_ipv4 and not has_ipv6:
                    continue

                groups.append(
                    {
                        "targets": [dns_name],
                        "labels": {
                            "__meta_cobbler_role": interface_name,
                            "__meta_cobbler_has_ipv4": "true" if has_ipv4 else "false",
                            "__meta_cobbler_has_ipv6": "true" if has_ipv6 else "false",
                            "__meta_cobbler_server": url,
                        },
                    }
                )

    return groups


class SDCache:
    """
    Rebuilds the HTTP SD group list at most once per `CACHE_TTL_SECONDS`, shared across
    concurrent requests.
    """

    def __init__(self, config_path: str, ttl_seconds: float):
        self._config_path = config_path
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._groups: List[Dict[str, Any]] = []
        self._last_refresh: Optional[float] = None

    def get_groups(self) -> List[Dict[str, Any]]:
        with self._lock:
            now = time.monotonic()
            if (
                self._last_refresh is None
                or (now - self._last_refresh) >= self._ttl_seconds
            ):
                try:
                    servers = load_server_config(self._config_path)
                    self._groups = build_sd_groups(servers)
                except (OSError, ValueError) as e:
                    logger.error("Failed to refresh Cobbler targets: %s", e)
                    # Keep serving the last known-good list rather than an error.
                self._last_refresh = now
            return self._groups


_cache = SDCache(CONFIG_PATH, CACHE_TTL_SECONDS)


class Handler(BaseHTTPRequestHandler):
    def _write_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload).encode("UTF-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        if self.path == "/sd":
            self._write_json(200, _cache.get_groups())
        elif self.path == "/healthz":
            self._write_json(200, {"status": "ok"})
        else:
            self._write_json(404, {"error": "not found"})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.info("%s - %s", self.address_string(), format % args)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), Handler)  # nosec: B104
    logger.info("cobbler-http-sd listening on :%s", LISTEN_PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
