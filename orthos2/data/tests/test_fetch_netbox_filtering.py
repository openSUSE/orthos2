"""Tests for interface name filtering in Machine.fetch_netbox()."""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from orthos2.data.models import NetworkInterface, ServerConfig
from orthos2.data.models.machine import Machine


def _make_interface(name: str, mac: str, iface_id: int) -> dict:
    return {
        "name": name,
        "id": iface_id,
        "primary_mac_address": {"mac_address": mac},
        "type": {"label": "1000BASE-T (1GE)"},
    }


def _make_netbox_api_mock(interfaces: list) -> MagicMock:
    mock = MagicMock()
    mock.check_interface_no_mgmt_by_id.return_value = interfaces
    mock.check_ip_by_interface_family.return_value = []
    mock.check_interface_mgmt_by_id.return_value = []
    return mock


NETBOX_MACHINE_RECORD = {
    "description": "test machine",
    "serial": "SN-001",
    "custom_fields": {"product_code": "PC-001"},
}


class FetchNetboxInterfaceFilteringTest(TestCase):
    """Machine.fetch_netbox() must skip interfaces with ignored name prefixes."""

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

    def _run_fetch(self, interfaces: list) -> None:
        mock_api = _make_netbox_api_mock(interfaces)
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

    def test_veth_interface_is_ignored(self) -> None:
        self._run_fetch([_make_interface("veth0", "00:00:00:00:00:01", 1)])
        assert not NetworkInterface.objects.filter(
            mac_address="00:00:00:00:00:01"
        ).exists()

    def test_flannel_interface_is_ignored(self) -> None:
        self._run_fetch([_make_interface("flannel0", "00:00:00:00:00:02", 2)])
        assert not NetworkInterface.objects.filter(
            mac_address="00:00:00:00:00:02"
        ).exists()

    def test_docker_interface_is_ignored(self) -> None:
        self._run_fetch([_make_interface("docker0", "00:00:00:00:00:03", 3)])
        assert not NetworkInterface.objects.filter(
            mac_address="00:00:00:00:00:03"
        ).exists()

    def test_usb_interface_is_ignored(self) -> None:
        self._run_fetch([_make_interface("usb0", "00:00:00:00:00:04", 4)])
        assert not NetworkInterface.objects.filter(
            mac_address="00:00:00:00:00:04"
        ).exists()

    def test_cali_interface_is_ignored(self) -> None:
        self._run_fetch([_make_interface("cali1234abcd", "00:00:00:00:00:05", 5)])
        assert not NetworkInterface.objects.filter(
            mac_address="00:00:00:00:00:05"
        ).exists()

    def test_tunl_interface_is_ignored(self) -> None:
        self._run_fetch([_make_interface("tunl0", "00:00:00:00:00:06", 6)])
        assert not NetworkInterface.objects.filter(
            mac_address="00:00:00:00:00:06"
        ).exists()

    def test_lo_interface_is_ignored(self) -> None:
        self._run_fetch([_make_interface("lo", "00:00:00:00:00:07", 7)])
        assert not NetworkInterface.objects.filter(
            mac_address="00:00:00:00:00:07"
        ).exists()

    def test_regular_eth_interface_is_registered(self) -> None:
        self._run_fetch([_make_interface("eth0", "11:22:33:44:55:66", 10)])
        assert NetworkInterface.objects.filter(mac_address="11:22:33:44:55:66").exists()

    def test_bond_interface_is_registered(self) -> None:
        self._run_fetch([_make_interface("bond0", "11:22:33:44:55:77", 11)])
        assert NetworkInterface.objects.filter(mac_address="11:22:33:44:55:77").exists()

    def test_ens_interface_is_registered(self) -> None:
        self._run_fetch([_make_interface("ens3", "11:22:33:44:55:88", 12)])
        assert NetworkInterface.objects.filter(mac_address="11:22:33:44:55:88").exists()

    def test_ignored_and_valid_interfaces_mixed(self) -> None:
        """Valid interfaces are created; ignored ones are not."""
        interfaces = [
            _make_interface("veth0", "AA:00:00:00:00:01", 20),
            _make_interface("eth1", "AA:00:00:00:00:02", 21),
            _make_interface("flannel0", "AA:00:00:00:00:03", 22),
            _make_interface("ens5", "AA:00:00:00:00:04", 23),
        ]
        self._run_fetch(interfaces)
        assert not NetworkInterface.objects.filter(
            mac_address="AA:00:00:00:00:01"
        ).exists()
        assert NetworkInterface.objects.filter(mac_address="AA:00:00:00:00:02").exists()
        assert not NetworkInterface.objects.filter(
            mac_address="AA:00:00:00:00:03"
        ).exists()
        assert NetworkInterface.objects.filter(mac_address="AA:00:00:00:00:04").exists()
