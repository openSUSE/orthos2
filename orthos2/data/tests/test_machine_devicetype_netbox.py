"""Tests for device_type resolution in Machine.fetch_netbox()."""

from unittest.mock import patch

from django.test import TestCase

from orthos2.data.models import Architecture, DeviceType, Machine, Manufacturer, System

NETBOX_DEVICE_RECORD = {
    "description": "",
    "serial": "",
    "custom_fields": {},
    "device_type": {
        "id": 6,
        "manufacturer": {"id": 4, "name": "AMD"},
        "model": "EPYC ROME",
    },
}

NETBOX_VM_RECORD = {
    "description": "",
    "serial": "",
    "custom_fields": {},
}


class FetchNetboxDeviceTypeTest(TestCase):
    fixtures = ["orthos2/data/fixtures/tests/test_domain_orthos2test.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AMD-Local", netbox_id=4)
        self.device_type = DeviceType.objects.create(
            name="EPYC ROME", manufacturer=self.manufacturer, netbox_id=6
        )
        self.machine = Machine.objects.create(
            fqdn="testmachine.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
            netbox_id=123,
        )

    def _fetch_netbox(self, netbox_record) -> None:
        with patch.object(
            self.machine, "fetch_netbox_record", return_value=netbox_record
        ), patch("orthos2.data.models.machine.Netbox") as mocked_netbox_cls, patch(
            "orthos2.data.models.machine.DeviceType.get_or_create_from_netbox"
        ) as mocked_resolver:
            mocked_netbox_instance = mocked_netbox_cls.get_instance.return_value
            mocked_netbox_instance.check_interface_no_mgmt_by_id.return_value = []
            mocked_netbox_instance.check_interface_mgmt_by_id.return_value = []
            mocked_resolver.return_value = self.device_type
            self.machine.fetch_netbox()
        self._mocked_resolver = mocked_resolver

    def test_resolves_device_type_when_unset(self) -> None:
        self._fetch_netbox(NETBOX_DEVICE_RECORD)

        self._mocked_resolver.assert_called_once_with(6)
        self.machine.refresh_from_db()
        assert self.machine.device_type_id == self.device_type.pk

    def test_skips_resolution_when_already_linked_to_same_device_type(self) -> None:
        self.machine.device_type = self.device_type
        self.machine.save()

        self._fetch_netbox(NETBOX_DEVICE_RECORD)

        self._mocked_resolver.assert_not_called()

    def test_reresolves_when_linked_device_type_differs(self) -> None:
        other_manufacturer = Manufacturer.objects.create(
            name="Other-Local", netbox_id=5
        )
        other_device_type = DeviceType.objects.create(
            name="Other Model", manufacturer=other_manufacturer, netbox_id=7
        )
        self.machine.device_type = other_device_type
        self.machine.save()

        self._fetch_netbox(NETBOX_DEVICE_RECORD)

        self._mocked_resolver.assert_called_once_with(6)
        self.machine.refresh_from_db()
        assert self.machine.device_type_id == self.device_type.pk

    def test_skips_resolution_for_vm_payload_without_device_type(self) -> None:
        self._fetch_netbox(NETBOX_VM_RECORD)

        self._mocked_resolver.assert_not_called()
        self.machine.refresh_from_db()
        assert self.machine.device_type is None
