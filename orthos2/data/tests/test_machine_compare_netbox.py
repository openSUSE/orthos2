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
