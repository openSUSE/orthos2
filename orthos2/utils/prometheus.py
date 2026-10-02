"""
Utility module that wraps functionality related to querying Prometheus. This talks to a
Prometheus server's HTTP API (not a specific exporter) to answer instant queries such as
`probe_success` for a given scrape job.
"""

import logging
from typing import Any, Dict, Optional

import requests

from orthos2 import settings

logger = logging.getLogger("utils")


class Prometheus:
    __object: Optional["Prometheus"] = None

    def __init__(self, host: str):
        self.base_url = host.rstrip("/")
        self.s = requests.Session()

    @classmethod
    def get_instance(cls) -> "Prometheus":
        if cls.__object is None:
            cls.__object = Prometheus(settings.PROMETHEUS_URL)
        return cls.__object

    def query_instant(self, promql: str) -> Dict[str, Any]:
        """
        Run a PromQL instant query against `{PROMETHEUS_URL}/api/v1/query`.
        """
        url = f"{self.base_url}/api/v1/query"
        logger.debug("HTTP Request: GET %s - query=%s", url, promql)
        response = self.s.get(url, params={"query": promql}, timeout=10)
        response.raise_for_status()
        return response.json()  # type: ignore

    def probe_success_map(self, job: str) -> Dict[str, bool]:
        """
        Fetch the current `probe_success` value for every instance scraped under the given job
        in a single query, so callers don't need to query once per target.

        :param job: Name of the Prometheus scrape job (e.g. "icmp-arch-ipv4").
        :returns: A mapping of instance (fqdn) to its latest probe_success state. Returns an
                  empty dict (instead of raising) if Prometheus isn't configured or unreachable,
                  so callers can degrade gracefully.
        """
        if not self.base_url:
            logger.warning(
                "ORTHOS2_PROMETHEUS_URL is not configured, skipping query for job '%s'",
                job,
            )
            return {}

        try:
            data = self.query_instant('probe_success{job="%s"}' % job)
        except (requests.RequestException, ValueError) as e:
            logger.warning("Failed to query Prometheus for job '%s': %s", job, e)
            return {}

        result: Dict[str, bool] = {}
        for entry in data.get("data", {}).get("result", []):
            instance = entry.get("metric", {}).get("instance")
            value = entry.get("value")
            if not instance or not value or len(value) != 2:
                continue
            result[instance] = value[1] == "1"
        return result
