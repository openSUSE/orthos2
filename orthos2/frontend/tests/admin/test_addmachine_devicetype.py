"""
Tests for device_type resolution in the "Add via NetBox ID" flow
(AddMachineFormView.form_valid()).
"""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Architecture, DeviceType, Machine, Manufacturer, System

NETBOX_DEVICE_RECORD = {
    "name": "newmachine.orthos2.test",
    "custom_fields": {"arch": "x86_64"},
    "device_type": {
        "id": 6,
        "manufacturer": {"id": 4, "name": "AMD"},
        "model": "EPYC ROME",
    },
}

NETBOX_VM_RECORD = {
    "name": "newvm.orthos2.test",
    "custom_fields": {"arch": "x86_64"},
}


class AddMachineDeviceTypeTest(TestCase):
    fixtures = [
        "orthos2/frontend/tests/user/fixtures/users.json",
        "orthos2/data/fixtures/tests/test_domain_orthos2test.json",
    ]

    def setUp(self) -> None:
        self.superuser = User.objects.get(username="superuser")
        self.system = System.objects.get(name="BareMetal")
        self.manufacturer = Manufacturer.objects.create(name="AMD-Local", netbox_id=4)
        self.device_type = DeviceType.objects.create(
            name="EPYC ROME", manufacturer=self.manufacturer, netbox_id=6
        )

    def _post_add_machine(self, netbox_object_type: str):
        self.client.force_login(self.superuser)
        return self.client.post(
            reverse("frontend:machine_add"),
            {
                "netbox_id": "123",
                "system": self.system.pk,
                "netbox_object_type": netbox_object_type,
            },
        )

    def test_new_device_gets_device_type_resolved(self) -> None:
        with patch(
            "orthos2.frontend.forms.addmachine.Netbox"
        ) as mocked_netbox_cls, patch(
            "orthos2.frontend.forms.addmachine.DeviceType.get_or_create_from_netbox"
        ) as mocked_resolver:
            mocked_netbox_cls.get_instance.return_value.fetch_device.return_value = (
                NETBOX_DEVICE_RECORD
            )
            mocked_resolver.return_value = self.device_type
            response = self._post_add_machine("device")

        assert response.status_code == 302
        mocked_resolver.assert_called_once_with(6)
        machine = Machine.objects.get(fqdn="newmachine.orthos2.test")
        assert machine.device_type_id == self.device_type.pk

    def test_existing_machine_matched_by_fqdn_gets_device_type_updated(self) -> None:
        existing_machine = Machine.objects.create(
            fqdn="newmachine.orthos2.test",
            system=self.system,
            architecture=Architecture.objects.get(name="x86_64"),
        )
        with patch(
            "orthos2.frontend.forms.addmachine.Netbox"
        ) as mocked_netbox_cls, patch(
            "orthos2.frontend.forms.addmachine.DeviceType.get_or_create_from_netbox"
        ) as mocked_resolver:
            mocked_netbox_cls.get_instance.return_value.fetch_device.return_value = (
                NETBOX_DEVICE_RECORD
            )
            mocked_resolver.return_value = self.device_type
            response = self._post_add_machine("device")

        assert response.status_code == 302
        mocked_resolver.assert_called_once_with(6)
        existing_machine.refresh_from_db()
        assert existing_machine.device_type_id == self.device_type.pk

    def test_vm_object_type_skips_device_type_resolution(self) -> None:
        with patch(
            "orthos2.frontend.forms.addmachine.Netbox"
        ) as mocked_netbox_cls, patch(
            "orthos2.frontend.forms.addmachine.DeviceType.get_or_create_from_netbox"
        ) as mocked_resolver:
            mocked_netbox_cls.get_instance.return_value.fetch_vm.return_value = (
                NETBOX_VM_RECORD
            )
            response = self._post_add_machine("vm")

        assert response.status_code == 302
        mocked_resolver.assert_not_called()
        machine = Machine.objects.get(fqdn="newvm.orthos2.test")
        assert machine.device_type is None
