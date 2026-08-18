"""Test module to ensure the functionality of the API forms."""

from django.test import TestCase

from orthos2.api.forms import (
    AnnotationAPIForm,
    BMCAPIForm,
    DeleteDeviceTypeAPIForm,
    DeleteMachineAPIForm,
    DeleteManufacturerAPIForm,
    DeleteRemotePowerAPIForm,
    DeleteRemotePowerDeviceAPIForm,
    DeleteSerialConsoleTypeAPIForm,
    DeviceTypeAPIForm,
    MachineAPIForm,
    ManufacturerAPIForm,
    RemotePowerAPIForm,
    RemotePowerDeviceAPIForm,
    ReserveMachineAPIForm,
    SerialConsoleAPIForm,
    SerialConsoleTypeAPIForm,
    VirtualMachineAPIForm,
)
from orthos2.data.models import DeviceType, Manufacturer, SerialConsoleType, System
from orthos2.data.models.machine import Machine
from orthos2.data.models.remotepowertype import RemotePowerType


class ReserveMachineAPIFormTests(TestCase):
    def test_form_with_date(self) -> None:
        """Test the machine reservation API form with a concrete date"""
        import datetime

        future_date = (datetime.date.today() + datetime.timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )
        form = ReserveMachineAPIForm(
            {"reason": "my reason", "until": future_date, "username": "testuser"}
        )

        self.assertTrue(form.is_valid())

    def test_form_permanently(self) -> None:
        """Test the machine reservation API form with permanently=True"""
        form = ReserveMachineAPIForm(
            {"reason": "my reason", "permanently": True, "username": "testuser"}
        )

        self.assertTrue(form.is_valid())


class VirtualMachineAPIFormTests(TestCase):
    fixtures = [
        "orthos2/data/fixtures/tests/test_machines.json",
        "orthos2/data/fixtures/systems.json",
    ]

    def test_form(self) -> None:
        """Test the virtual machine creation API form"""
        # Arrange & Act
        host = Machine.objects.get_by_natural_key("test.testing.suse.de")  # type: ignore
        system_id = System.objects.get(name="VM KVM").id
        form = VirtualMachineAPIForm(
            {
                "architecture": "x86_64",
                "system": system_id,
                "ram_amount": "2048",
                "disk_size": "30",
                "image": "none",
                "networkinterfaces": "2",
            },
            **{"virtualization_api": host.virtualization_api}  # type: ignore
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
        self.assertTrue(form.is_valid())


class DeleteMachineAPIFormTests(TestCase):

    fixtures = [
        "orthos2/data/fixtures/systems.json",
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
    fixtures = [
        "orthos2/api/fixtures/forms/create_bmc_api_form.json",
    ]

    def test_form(self) -> None:
        """Test the BMC creation API form"""
        # Arrange & Act
        agent = RemotePowerType.objects.get(name="ipmilanplus")
        form = BMCAPIForm(
            {
                "fqdn": "test.foo.de",
                "mac": "AA:BB:CC:DD:EE",
                "fence_agent": agent.id,
            }
        )

        # Assert
        self.assertTrue(form.is_valid())


class RemotePowerAPIFormTests(TestCase):
    fixtures = [
        "orthos2/api/fixtures/forms/create_remote_power_api_form.json",
    ]

    def test_form(self) -> None:
        """Test the remote power creation API form"""
        # Arrange & Act
        form = RemotePowerAPIForm(
            {"fence_agent": "", "remote_power_device": "", "port": ""}
        )

        # Assert
        self.assertTrue(form.is_valid())


class RemotePowerDeviceAPIFormTests(TestCase):
    fixtures = [
        "orthos2/api/fixtures/forms/create_remote_power_device_api_form.json",
    ]

    def test_form(self) -> None:
        """Test the remote power device creation API form"""
        # Arrange & Act
        agent = RemotePowerType.objects.get(name="apc")
        form = RemotePowerDeviceAPIForm(
            {
                "fqdn": "TODO",
                "password": "test",
                "mac": "AA:BB:CC:DD:EE:FF",
                "username": "TODO",
                "fence_agent": agent.id,
                "architecture": 1,
            }
        )

        # Assert
        self.assertTrue(form.is_valid())


class DeleteRemotePowerAPIFormTests(TestCase):

    fixtures = [
        "orthos2/data/fixtures/systems.json",
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


class ManufacturerAPIFormTests(TestCase):
    def test_form(self) -> None:
        """Test the manufacturer creation API form"""
        # Arrange & Act
        form = ManufacturerAPIForm({"name": "AcmeCorp"})

        # Assert
        self.assertTrue(form.is_valid())

    def test_form_requires_name(self) -> None:
        """Test that the manufacturer creation API form requires a name"""
        # Arrange & Act
        form = ManufacturerAPIForm({"name": ""})

        # Assert
        self.assertFalse(form.is_valid())


class DeleteManufacturerAPIFormTests(TestCase):
    def test_form(self) -> None:
        """Test the manufacturer deletion API form"""
        # Arrange
        Manufacturer.objects.create(name="AcmeCorp")

        # Act
        form = DeleteManufacturerAPIForm({"name": "AcmeCorp"})

        # Assert
        self.assertTrue(form.is_valid())

    def test_form_rejects_nonexistent_manufacturer(self) -> None:
        """Test that the manufacturer deletion API form rejects an unknown name"""
        # Arrange & Act
        form = DeleteManufacturerAPIForm({"name": "Nonexistent"})

        # Assert
        self.assertFalse(form.is_valid())


class DeviceTypeAPIFormTests(TestCase):
    def test_form(self) -> None:
        """Test the device type creation API form"""
        # Arrange
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")

        # Act
        form = DeviceTypeAPIForm(
            {"name": "AcmeDeviceType", "manufacturer": manufacturer.pk}
        )

        # Assert
        self.assertTrue(form.is_valid())

    def test_form_requires_name(self) -> None:
        """Test that the device type creation API form requires a name"""
        # Arrange
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")

        # Act
        form = DeviceTypeAPIForm({"name": "", "manufacturer": manufacturer.pk})

        # Assert
        self.assertFalse(form.is_valid())


class DeleteDeviceTypeAPIFormTests(TestCase):
    def test_form(self) -> None:
        """Test the device type deletion API form"""
        # Arrange
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        DeviceType.objects.create(name="AcmeDeviceType", manufacturer=manufacturer)

        # Act
        form = DeleteDeviceTypeAPIForm({"name": "AcmeDeviceType"})

        # Assert
        self.assertTrue(form.is_valid())

    def test_form_rejects_nonexistent_devicetype(self) -> None:
        """Test that the device type deletion API form rejects an unknown name"""
        # Arrange & Act
        form = DeleteDeviceTypeAPIForm({"name": "Nonexistent"})

        # Assert
        self.assertFalse(form.is_valid())


class SerialConsoleTypeAPIFormTests(TestCase):
    def test_form(self) -> None:
        """Test the serial console type creation API form"""
        # Arrange & Act
        form = SerialConsoleTypeAPIForm({"name": "AcmeConsole"})

        # Assert
        self.assertTrue(form.is_valid())

    def test_form_requires_name(self) -> None:
        """Test that the serial console type creation API form requires a name"""
        # Arrange & Act
        form = SerialConsoleTypeAPIForm({"name": ""})

        # Assert
        self.assertFalse(form.is_valid())


class DeleteSerialConsoleTypeAPIFormTests(TestCase):
    def test_form(self) -> None:
        """Test the serial console type deletion API form"""
        # Arrange
        SerialConsoleType.objects.create(name="AcmeConsole")

        # Act
        form = DeleteSerialConsoleTypeAPIForm({"name": "AcmeConsole"})

        # Assert
        self.assertTrue(form.is_valid())

    def test_form_rejects_nonexistent_serialconsoletype(self) -> None:
        """Test that the serial console type deletion API form rejects an unknown name"""
        # Arrange & Act
        form = DeleteSerialConsoleTypeAPIForm({"name": "Nonexistent"})

        # Assert
        self.assertFalse(form.is_valid())
