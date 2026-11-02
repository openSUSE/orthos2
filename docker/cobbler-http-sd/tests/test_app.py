import json
import sys
import xmlrpc.client
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app  # noqa: E402

INTERFACES_HOST1_BOTH = [
    {
        "name": "host1-default",
        "mac_address": "00:11:22:33:44:01",
        "dns": {"name": "host1.example.org"},
        "ipv4": {"address": "10.0.0.1"},
        "ipv6": {"address": ""},
    },
    {
        "name": "host1-bmc",
        "mac_address": "00:11:22:33:44:02",
        "dns": {"name": "host1-sp.example.org"},
        "ipv4": {"address": "10.0.0.2"},
        "ipv6": {"address": ""},
    },
]

INTERFACES_UNKNOWN_ROLE = [
    {
        "name": "weird-eth1",
        "mac_address": "00:11:22:33:44:03",
        "dns": {"name": "weird-eth1.example.org"},
        "ipv4": {"address": "10.0.0.3"},
        "ipv6": {"address": ""},
    },
]

INTERFACES_WITHOUT_ADDRESSES = [
    {
        "name": "noaddr-default",
        "mac_address": "00:11:22:33:44:04",
        "dns": {"name": "noaddr.example.org"},
        "ipv4": {"address": ""},
        "ipv6": {"address": ""},
    },
]


def test_build_sd_groups_normal_parse():
    with patch.object(
        app, "fetch_network_interfaces", return_value=INTERFACES_HOST1_BOTH
    ):
        groups = app.build_sd_groups(
            [{"url": "http://cobbler.example.com/cobbler_api"}]
        )

    assert len(groups) == 2

    by_target = {g["targets"][0]: g for g in groups}
    host_group = by_target["host1.example.org"]
    assert host_group["labels"]["__meta_cobbler_role"] == "default"
    assert host_group["labels"]["__meta_cobbler_has_ipv4"] == "true"
    assert host_group["labels"]["__meta_cobbler_has_ipv6"] == "false"

    bmc_group = by_target["host1-sp.example.org"]
    assert bmc_group["labels"]["__meta_cobbler_role"] == "bmc"


def test_build_sd_groups_skips_unknown_interfaces_and_empty_addresses():
    with patch.object(
        app,
        "fetch_network_interfaces",
        return_value=INTERFACES_UNKNOWN_ROLE + INTERFACES_WITHOUT_ADDRESSES,
    ):
        groups = app.build_sd_groups(
            [{"url": "http://cobbler.example.com/cobbler_api"}]
        )

    assert groups == []


def test_build_sd_groups_skips_a_server_that_errors_but_keeps_others():
    def fake_fetch(server):
        if server["url"] == "http://down.example.com/cobbler_api":
            raise OSError("connection refused")
        return INTERFACES_HOST1_BOTH

    with patch.object(app, "fetch_network_interfaces", side_effect=fake_fetch):
        groups = app.build_sd_groups(
            [
                {"url": "http://down.example.com/cobbler_api"},
                {"url": "http://up.example.com/cobbler_api"},
            ]
        )

    assert len(groups) == 2


def test_build_sd_groups_empty_server_list_returns_empty_list():
    assert app.build_sd_groups([]) == []


def test_fetch_network_interfaces_anonymous_when_no_credentials():
    proxy = MagicMock()
    proxy.get_network_interfaces.return_value = INTERFACES_HOST1_BOTH

    with patch.object(xmlrpc.client, "ServerProxy", return_value=proxy):
        interfaces = app.fetch_network_interfaces(
            {"url": "http://cobbler.example.com/cobbler_api"}
        )

    proxy.login.assert_not_called()
    assert interfaces == INTERFACES_HOST1_BOTH


def test_fetch_network_interfaces_logs_in_when_credentials_present():
    proxy = MagicMock()
    proxy.get_network_interfaces.return_value = []

    with patch.object(xmlrpc.client, "ServerProxy", return_value=proxy):
        app.fetch_network_interfaces(
            {
                "url": "http://cobbler.example.com/cobbler_api",
                "username": "testuser",
                "password": "testpass",
            }
        )

    proxy.login.assert_called_once_with("testuser", "testpass")


def test_fetch_network_interfaces_raises_on_non_list_result():
    proxy = MagicMock()
    proxy.get_network_interfaces.return_value = {"not": "a list"}

    with patch.object(xmlrpc.client, "ServerProxy", return_value=proxy):
        with pytest.raises(ValueError):
            app.fetch_network_interfaces(
                {"url": "http://cobbler.example.com/cobbler_api"}
            )


def test_load_server_config(tmp_path):
    config_path = tmp_path / "servers.json"
    config_path.write_text(
        json.dumps([{"url": "http://cobbler.example.com/cobbler_api"}])
    )

    servers = app.load_server_config(str(config_path))

    assert servers == [{"url": "http://cobbler.example.com/cobbler_api"}]


def test_load_server_config_rejects_non_list(tmp_path):
    config_path = tmp_path / "servers.json"
    config_path.write_text(json.dumps({"not": "a list"}))

    with pytest.raises(ValueError):
        app.load_server_config(str(config_path))


def test_sd_cache_refreshes_only_after_ttl_expires(tmp_path):
    config_path = tmp_path / "servers.json"
    config_path.write_text(
        json.dumps([{"url": "http://cobbler.example.com/cobbler_api"}])
    )

    cache = app.SDCache(str(config_path), ttl_seconds=3600)

    with patch.object(app, "build_sd_groups", return_value=["first"]) as build_mock:
        assert cache.get_groups() == ["first"]
        assert cache.get_groups() == ["first"]
        assert build_mock.call_count == 1


def test_sd_cache_keeps_last_good_result_on_refresh_error(tmp_path):
    config_path = tmp_path / "servers.json"
    config_path.write_text(
        json.dumps([{"url": "http://cobbler.example.com/cobbler_api"}])
    )

    cache = app.SDCache(str(config_path), ttl_seconds=0)

    with patch.object(app, "build_sd_groups", return_value=["good"]):
        assert cache.get_groups() == ["good"]

    with patch.object(app, "load_server_config", side_effect=OSError("gone")):
        assert cache.get_groups() == ["good"]
