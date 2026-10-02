from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings

from orthos2.utils.prometheus import Prometheus

SAMPLE_RESPONSE = {
    "status": "success",
    "data": {
        "resultType": "vector",
        "result": [
            {
                "metric": {"instance": "host1.example.org", "job": "icmp-arch-ipv4"},
                "value": [1700000000, "1"],
            },
            {
                "metric": {
                    "instance": "host1-sp.example.org",
                    "job": "icmp-arch-ipv4",
                },
                "value": [1700000000, "0"],
            },
        ],
    },
}


class PrometheusProbeSuccessMapTest(TestCase):
    def setUp(self) -> None:
        self.prometheus = Prometheus("https://prometheus.example.com")

    def test_probe_success_map_parses_reachable_and_unreachable(self) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status.return_value = None

        with patch.object(self.prometheus.s, "get", return_value=mock_response):
            result = self.prometheus.probe_success_map("icmp-arch-ipv4")

        self.assertEqual(
            result,
            {
                "host1.example.org": True,
                "host1-sp.example.org": False,
            },
        )

    def test_probe_success_map_returns_empty_dict_on_empty_result(self) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "data": {"result": []}}
        mock_response.raise_for_status.return_value = None

        with patch.object(self.prometheus.s, "get", return_value=mock_response):
            result = self.prometheus.probe_success_map("icmp-arch-ipv4")

        self.assertEqual(result, {})

    def test_probe_success_map_returns_empty_dict_on_request_error(self) -> None:
        with patch.object(
            self.prometheus.s, "get", side_effect=requests.ConnectionError("down")
        ):
            result = self.prometheus.probe_success_map("icmp-arch-ipv4")

        self.assertEqual(result, {})

    def test_probe_success_map_skips_query_when_url_not_configured(self) -> None:
        prometheus = Prometheus("")

        with patch.object(prometheus.s, "get") as get_mock:
            result = prometheus.probe_success_map("icmp-arch-ipv4")

        get_mock.assert_not_called()
        self.assertEqual(result, {})

    @override_settings(PROMETHEUS_URL="https://prometheus.example.com")
    def test_get_instance_returns_singleton(self) -> None:
        Prometheus._Prometheus__object = None  # type: ignore[attr-defined]  # reset singleton between tests
        first = Prometheus.get_instance()
        second = Prometheus.get_instance()
        self.assertIs(first, second)
