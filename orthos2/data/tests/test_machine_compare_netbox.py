"""Tests for Machine.compare_netbox()."""

from unittest.mock import patch

from django.test import TestCase

from orthos2.data.models import Architecture, Machine, System
from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionResult


class CompareNetboxArchitectureTest(TestCase):
    fixtures = ["orthos2/data/fixtures/tests/test_domain_orthos2test.json"]

    def setUp(self) -> None:
        self.machine = Machine.objects.create(
            fqdn="testmachine.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
            netbox_id=123,
        )

    def test_explicit_null_arch_custom_field_does_not_raise(self) -> None:
        """NetBox serializes an unset custom field as an explicit `null`, not
        a missing key -- compare_netbox() must not pass that None straight
        into the non-nullable netbox_result column."""
        netbox_record = {
            "description": "",
            "custom_fields": {"arch": None},
        }
        with patch.object(
            self.machine, "fetch_netbox_record", return_value=netbox_record
        ):
            self.machine.compare_netbox()

        result = NetboxOrthosComparisionResult.objects.get(
            run_id__object_machine=self.machine, property_name="architecture"
        )
        assert result.orthos_result == "x86_64"
        assert result.netbox_result == "<not set>"

    def test_arch_custom_field_as_value_label_subobject_resolves_to_value(
        self,
    ) -> None:
        """NetBox 4.7+ serializes a set custom select field as a
        `{"value": ..., "label": ...}` sub-object instead of a plain scalar."""
        netbox_record = {
            "description": "",
            "custom_fields": {"arch": {"value": "x86_64", "label": "x86_64"}},
        }
        with patch.object(
            self.machine, "fetch_netbox_record", return_value=netbox_record
        ):
            self.machine.compare_netbox()

        result = NetboxOrthosComparisionResult.objects.get(
            run_id__object_machine=self.machine, property_name="architecture"
        )
        assert result.netbox_result == "x86_64"

    def test_serial_number_and_product_code_are_compared(self) -> None:
        self.machine.serial_number = "SN-001"
        self.machine.product_code = "PC-001"
        self.machine.save()
        netbox_record = {
            "description": "",
            "serial": "SN-002",
            "custom_fields": {"arch": None, "product_code": "PC-002"},
        }
        with patch.object(
            self.machine, "fetch_netbox_record", return_value=netbox_record
        ):
            self.machine.compare_netbox()

        serial_result = NetboxOrthosComparisionResult.objects.get(
            run_id__object_machine=self.machine, property_name="serial_number"
        )
        assert serial_result.orthos_result == "SN-001"
        assert serial_result.netbox_result == "SN-002"

        product_code_result = NetboxOrthosComparisionResult.objects.get(
            run_id__object_machine=self.machine, property_name="product_code"
        )
        assert product_code_result.orthos_result == "PC-001"
        assert product_code_result.netbox_result == "PC-002"

    def test_serial_number_and_product_code_default_to_not_set(self) -> None:
        netbox_record = {
            "description": "",
            "custom_fields": {"arch": None},
        }
        with patch.object(
            self.machine, "fetch_netbox_record", return_value=netbox_record
        ):
            self.machine.compare_netbox()

        serial_result = NetboxOrthosComparisionResult.objects.get(
            run_id__object_machine=self.machine, property_name="serial_number"
        )
        assert serial_result.orthos_result == "<not set>"
        assert serial_result.netbox_result == "<not set>"

        product_code_result = NetboxOrthosComparisionResult.objects.get(
            run_id__object_machine=self.machine, property_name="product_code"
        )
        assert product_code_result.orthos_result == "<not set>"
        assert product_code_result.netbox_result == "<not set>"

    def test_cpu_and_ram_compared_for_physical_machine(self) -> None:
        self.machine.cpu_physical = 2
        self.machine.cpu_cores = 64
        self.machine.cpu_threads = 128
        self.machine.ram_amount = 524288
        self.machine.save()
        netbox_record = {
            "description": "",
            "custom_fields": {
                "arch": None,
                "cpu_sockets": 2,
                "cpu_cores": 64,
                "cpu_threads": 128,
                "ram_amount": 524288,
            },
        }
        with patch.object(
            self.machine, "fetch_netbox_record", return_value=netbox_record
        ):
            self.machine.compare_netbox()

        for property_name, expected in (
            ("cpu_sockets", "2"),
            ("cpu_cores", "64"),
            ("cpu_threads", "128"),
            ("ram_amount", "524288"),
        ):
            result = NetboxOrthosComparisionResult.objects.get(
                run_id__object_machine=self.machine, property_name=property_name
            )
            assert result.orthos_result == expected
            assert result.netbox_result == expected

    def test_cpu_and_ram_default_to_not_set_when_missing_from_netbox(self) -> None:
        netbox_record = {
            "description": "",
            "custom_fields": {"arch": None},
        }
        with patch.object(
            self.machine, "fetch_netbox_record", return_value=netbox_record
        ):
            self.machine.compare_netbox()

        for property_name in (
            "cpu_sockets",
            "cpu_cores",
            "cpu_threads",
            "ram_amount",
        ):
            result = NetboxOrthosComparisionResult.objects.get(
                run_id__object_machine=self.machine, property_name=property_name
            )
            assert result.netbox_result == "<not set>"

    def test_cpu_and_ram_are_not_compared_for_virtual_machine(self) -> None:
        """CPU topology and RAM custom fields only exist on NetBox Device
        objects, not VirtualMachine objects -- skip the comparison entirely
        for virtual machines."""
        vm_machine = Machine.objects.create(
            fqdn="testvm.orthos2.test",
            system=System.objects.get(name="VM KVM"),
            architecture=Architecture.objects.get(name="x86_64"),
            netbox_id=456,
        )
        netbox_record = {
            "description": "",
            "custom_fields": {"arch": None},
        }
        with patch.object(
            vm_machine, "fetch_netbox_record", return_value=netbox_record
        ):
            vm_machine.compare_netbox()

        assert not NetboxOrthosComparisionResult.objects.filter(
            run_id__object_machine=vm_machine, property_name="cpu_sockets"
        ).exists()
