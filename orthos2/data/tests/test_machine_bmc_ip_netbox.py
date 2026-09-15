"""Tests for BMC IP address parsing in Machine.fetch_netbox()."""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from orthos2.data.models import BMC, ServerConfig
from orthos2.data.models.machine import Machine

NETBOX_MACHINE_RECORD = {
    "description": "test machine",
    "serial": "SN-001",
    "custom_fields": {"product_code": "PC-001"},
}

MGMT_INTERFACE = {
    "id": 99,
    "primary_mac_address": {"mac_address": "AA:BB:CC:DD:EE:01"},
    "custom_fields": {"fence_agent": "ipmilanplus"},
}


def _make_netbox_api_mock(ipv4_addresses: list, ipv6_addresses: list) -> MagicMock:
    mock = MagicMock()
    mock.check_interface_no_mgmt_by_id.return_value = []
    mock.check_interface_mgmt_by_id.return_value = [MGMT_INTERFACE]

    def _check_ip_by_interface_family(interface_id: int, family: int) -> list:
        return ipv4_addresses if family == 4 else ipv6_addresses

    mock.check_ip_by_interface_family.side_effect = _check_ip_by_interface_family
    return mock


class FetchNetboxBmcIpTest(TestCase):
    """Machine.fetch_netbox() must not choke on non-network-aligned BMC IPs."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
    ]

    def setUp(self) -> None:
        ServerConfig.objects.update_or_create(
            key="domain.validendings", defaults={"value": "orthos2.test"}
        )
        Machine.objects.filter(pk=1).update(netbox_id=42)
        self.machine = Machine.objects.get(pk=1)
        # machine.save() inside fetch_netbox() rejects BareMetal machines with a BMC
        if hasattr(self.machine, "bmc"):
            self.machine.bmc.delete()
            self.machine = Machine.objects.get(pk=1)

    def _run_fetch(self, ipv4_addresses: list, ipv6_addresses: list) -> None:
        mock_api = _make_netbox_api_mock(ipv4_addresses, ipv6_addresses)
        with (
            patch(
                "orthos2.data.models.machine.Netbox.get_instance",
                return_value=mock_api,
            ),
            patch.object(
                self.machine,
                "fetch_netbox_record",
                return_value=NETBOX_MACHINE_RECORD,
            ),
        ):
            self.machine.fetch_netbox()

    def test_non_network_aligned_ipv4_is_stripped_not_raised(self) -> None:
        """A host address like 10.124.137.67/22 must not raise ValueError."""
        self._run_fetch(
            ipv4_addresses=[
                {"address": "10.124.137.67/22", "dns_name": "bmc.orthos2.test"}
            ],
            ipv6_addresses=[],
        )

        bmc = BMC.objects.get(mac="AA:BB:CC:DD:EE:01")
        assert bmc.ip_address_v4 == "10.124.137.67"

    def test_non_network_aligned_ipv6_is_stripped_not_raised(self) -> None:
        self._run_fetch(
            ipv4_addresses=[],
            ipv6_addresses=[
                {"address": "2001:db8::67/22", "dns_name": "bmc.orthos2.test"}
            ],
        )

        bmc = BMC.objects.get(mac="AA:BB:CC:DD:EE:01")
        assert bmc.ip_address_v6 == "2001:db8::67"
