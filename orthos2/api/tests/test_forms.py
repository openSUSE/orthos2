"""Test module to ensure the functionality of the API forms."""

from django.test import TestCase, override_settings

from orthos2.api.forms import (
    AnnotationAPIForm,
    BMCAPIForm,
    DeleteMachineAPIForm,
    DeleteRemotePowerAPIForm,
    DeleteRemotePowerDeviceAPIForm,
    MachineAPIForm,
    RemotePowerAPIForm,
    RemotePowerDeviceAPIForm,
    ReserveMachineAPIForm,
    SerialConsoleAPIForm,
    VirtualMachineAPIForm,
)
from orthos2.data.models.machine import Machine


class ReserveMachineAPIFormTests(TestCase):
    def test_form(self) -> None:
        """Test the machine reservation API form"""
        # Arrange & Act
        form = ReserveMachineAPIForm(
            {"reason": "my reason", "until": "9999-12-31", "user": "testuser"}
        )

        # Assert
        self.assertTrue(form.is_valid())


class VirtualMachineAPIFormTests(TestCase):
    fixtures = [
        "orthos2/data/fixtures/vendors.json",
        "orthos2/data/fixtures/tests/test_machines.json",
        "orthos2/data/fixtures/systems.json",
    ]

    def test_form(self) -> None:
        """Test the virtual machine creation API form"""
        # Arrange & Act
        host = Machine.objects.get_by_natural_key("test.testing.suse.de")
        form = VirtualMachineAPIForm(
            {
                "architecture": "x86_64",
                "system": "2",
                "ram_amount": "2048",
                "disk_size": "30",
                "image": "none",
                "networkinterfaces": "2",
            },
            **{"virtualization_api": host.virtualization_api}
        )

        # Assert
        self.assertTrue(form.is_valid())


class MachineAPIFormTests(TestCase):
    fixtures = [
        "orthos2/data/fixtures/architectures.json",
        "orthos2/data/fixtures/systems.json",
        "orthos2/data/fixtures/tests/test_serverconfig_domainending.json",
    ]

    def test_form(self) -> None:
        """Test the machine creation API form"""
        # Arrange & Act
        form = MachineAPIForm(
            {
                "fqdn": "test.foo.de",
                "enclosure": "",
                "architecture_id": "1",
                "system_id": "1",
                "group_id": "none",
                "check_connectivity": "3",
            }
        )
        # This is removing the "validate_dns" validator, mocking this is not
        # possible since the validator is part of the class definition.
        form.fields["fqdn"].validators.pop(0)

        # Assert
        print(form.errors)
        self.assertTrue(form.is_valid())


class DeleteMachineAPIFormTests(TestCase):

    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/data/fixtures/vendors.json",
        "orthos2/data/fixtures/tests/test_machines.json",
    ]

    def test_form(self) -> None:
        """test the machine deletion API form"""
        # Arrange & Act
        form = DeleteMachineAPIForm({"fqdn": "test.testing.suse.de"})

        # Assert
        self.assertTrue(form.is_valid())


class SerialConsoleAPIFormTests(TestCase):
    fixtures = ["orthos2/data/fixtures/serialconsoletypes.json"]

    def test_form(self) -> None:
        """Test the serial console creation API form"""
        # Arrange & Act
        form = SerialConsoleAPIForm(
            {
                "stype": "1",
                "baud_rate": "57600",
                "kernel_device": "ttyS",
                "kernel_device_num": "5",
            }
        )

        # Assert
        self.assertTrue(form.is_valid())


class AnnotationAPIFormTests(TestCase):
    def test_form(self) -> None:
        """Test the annotation creation API form"""
        # Arrange & Act
        form = AnnotationAPIForm({"text": "example text with lorem ipsum"})

        # Assert
        self.assertTrue(form.is_valid())


class BMCAPIFormTests(TestCase):
    remote_power_types = [
        {
            "fence": "ipmilanplus",
            "device": "bmc",
            "username": "xxx",
            "password": "XXX",
            "arch": ["x86_64", "aarch64"],
            "system": ["Bare Metal"],
        },
    ]

    @override_settings(REMOTEPOWER_TYPES=remote_power_types)
    def test_form(self) -> None:
        """Test the BMC creation API form"""
        # Arrange & Act
        form = BMCAPIForm(
            {
                "fqdn": "test.foo.de",
                "mac": "AA:BB:CC:DD:EE",
                "fence_name": "ipmilanplus",
            }
        )

        # Assert
        self.assertTrue(form.is_valid())


class RemotePowerAPIFormTests(TestCase):
    def test_form(self) -> None:
        """Test the remote power creation API form"""
        # Arrange & Act
        form = RemotePowerAPIForm(
            {"fence_name": "", "remote_power_device": "", "port": ""}
        )

        # Assert
        self.assertTrue(form.is_valid())


class RemotePowerDeviceAPIFormTests(TestCase):
    remote_power_types = [
        {
            "fence": "apc",
            "device": "rpower_device",
            "username": "xxx",
            "password": "XXX",
            "port": True,
            "system": ["Bare Metal"],
        },
    ]

    @override_settings(REMOTEPOWER_TYPES=remote_power_types)
    def test_form(self) -> None:
        """Test the remote power device creation API form"""
        # Arrange & Act
        form = RemotePowerDeviceAPIForm(
            {
                "fqdn": "TODO",
                "password": "test",
                "mac": "AA:BB:CC:DD:EE",
                "username": "TODO",
                "fence_name": "apc",
            }
        )

        # Assert
        self.assertTrue(form.is_valid())


class DeleteRemotePowerAPIFormTests(TestCase):

    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/data/fixtures/vendors.json",
        "orthos2/data/fixtures/tests/test_machines.json",
    ]

    def test_form(self) -> None:
        """Test the remote power deletion API form"""
        # Arrange & Act
        form = DeleteRemotePowerAPIForm({"fqdn": "test.testing.suse.de"})

        # Assert
        self.assertTrue(form.is_valid())


class DeleteRemotePowerDeviceAPIFormTests(TestCase):

    fixtures = ["orthos2/api/fixtures/forms/delete_remote_power_device_api_form.json"]

    def test_form(self) -> None:
        """Test the remote power device deletion API form"""
        # Arrange & Act
        form = DeleteRemotePowerDeviceAPIForm({"fqdn": "rpower.foo.de"})

        # Assert
        self.assertTrue(form.is_valid())
