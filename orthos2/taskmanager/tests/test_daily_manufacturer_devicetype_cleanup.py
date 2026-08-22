"""Tests for DailyManufacturerDeviceTypeCleanup."""

from django.test import TestCase

from orthos2.data.models import (
    Architecture,
    DeviceType,
    Enclosure,
    Machine,
    Manufacturer,
    System,
)
from orthos2.taskmanager.tasks.daily import DailyManufacturerDeviceTypeCleanup


class DailyManufacturerDeviceTypeCleanupTest(TestCase):
    fixtures = ["orthos2/data/fixtures/tests/test_domain_orthos2test.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_deletes_devicetype_referenced_by_nothing(self) -> None:
        DeviceType.objects.create(name="Unused", manufacturer=self.manufacturer)

        DailyManufacturerDeviceTypeCleanup().execute()

        assert not DeviceType.objects.filter(name="Unused").exists()

    def test_keeps_devicetype_referenced_by_machine(self) -> None:
        device_type = DeviceType.objects.create(
            name="InUse", manufacturer=self.manufacturer
        )
        Machine.objects.create(
            fqdn="testmachine.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
            device_type=device_type,
        )

        DailyManufacturerDeviceTypeCleanup().execute()

        assert DeviceType.objects.filter(pk=device_type.pk).exists()

    def test_keeps_devicetype_referenced_by_enclosure(self) -> None:
        device_type = DeviceType.objects.create(
            name="InUse", manufacturer=self.manufacturer
        )
        Enclosure.objects.create(name="testenclosure", device_type=device_type)

        DailyManufacturerDeviceTypeCleanup().execute()

        assert DeviceType.objects.filter(pk=device_type.pk).exists()

    def test_deletes_manufacturer_with_no_devicetypes(self) -> None:
        DailyManufacturerDeviceTypeCleanup().execute()

        assert not Manufacturer.objects.filter(pk=self.manufacturer.pk).exists()

    def test_keeps_manufacturer_with_a_remaining_devicetype(self) -> None:
        device_type = DeviceType.objects.create(
            name="InUse", manufacturer=self.manufacturer
        )
        Machine.objects.create(
            fqdn="testmachine.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
            device_type=device_type,
        )

        DailyManufacturerDeviceTypeCleanup().execute()

        assert Manufacturer.objects.filter(pk=self.manufacturer.pk).exists()

    def test_manufacturer_orphaned_by_this_same_run_is_also_deleted(self) -> None:
        """
        DeviceType cleanup must run before Manufacturer cleanup: a
        Manufacturer whose only DeviceType gets deleted in this same
        execute() call should be deleted too, not left behind for the next
        run.
        """
        DeviceType.objects.create(name="Unused", manufacturer=self.manufacturer)

        DailyManufacturerDeviceTypeCleanup().execute()

        assert not Manufacturer.objects.filter(pk=self.manufacturer.pk).exists()
