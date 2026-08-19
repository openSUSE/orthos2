"""Tests for Manufacturer.fetch_netbox() and Manufacturer.compare_netbox()."""

from unittest.mock import patch

from django.test import TestCase

from orthos2.data.models import Manufacturer
from orthos2.data.models.netboxorthoscomparision import (
    NetboxOrthosComparisionResult,
    NetboxOrthosComparisionRun,
)

NETBOX_MANUFACTURER_RECORD = {
    "id": 42,
    "name": "Acme Corp",
    "description": "Updated by NetBox",
}


class FetchNetboxTest(TestCase):
    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp", netbox_id=42)

    def test_skips_when_netbox_id_is_zero(self) -> None:
        manufacturer = Manufacturer.objects.create(name="NoNetbox", netbox_id=0)
        with patch.object(manufacturer, "fetch_netbox_record") as mocked_fetch:
            manufacturer.fetch_netbox()
        mocked_fetch.assert_not_called()

    def test_overwrites_name_and_description(self) -> None:
        with patch.object(
            self.manufacturer,
            "fetch_netbox_record",
            return_value=NETBOX_MANUFACTURER_RECORD,
        ):
            self.manufacturer.fetch_netbox()

        self.manufacturer.refresh_from_db()
        assert self.manufacturer.name == "Acme Corp"
        assert self.manufacturer.description == "Updated by NetBox"
        assert self.manufacturer.netbox_last_fetch_attempt is not None

    def test_stamps_fetch_attempt_even_when_record_not_found(self) -> None:
        with patch.object(self.manufacturer, "fetch_netbox_record", return_value=None):
            self.manufacturer.fetch_netbox()

        self.manufacturer.refresh_from_db()
        assert self.manufacturer.name == "AcmeCorp"
        assert self.manufacturer.netbox_last_fetch_attempt is not None


class CompareNetboxTest(TestCase):
    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp", netbox_id=42)

    def test_skips_when_netbox_id_is_zero(self) -> None:
        manufacturer = Manufacturer.objects.create(name="NoNetbox", netbox_id=0)
        manufacturer.compare_netbox()
        assert NetboxOrthosComparisionRun.objects.count() == 0

    def test_creates_run_and_results(self) -> None:
        with patch.object(
            self.manufacturer,
            "fetch_netbox_record",
            return_value=NETBOX_MANUFACTURER_RECORD,
        ):
            self.manufacturer.compare_netbox()

        run = NetboxOrthosComparisionRun.objects.get(
            object_manufacturer=self.manufacturer
        )
        assert (
            run.object_type
            == NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.MANUFACTURER
        )

        results = {
            result.property_name: result
            for result in NetboxOrthosComparisionResult.objects.filter(run_id=run)
        }
        assert results["name"].orthos_result == "AcmeCorp"
        assert results["name"].netbox_result == "Acme Corp"
        assert results["description"].orthos_result == "<not set>"
        assert results["description"].netbox_result == "Updated by NetBox"

        # compare_netbox must not mutate the manufacturer itself
        self.manufacturer.refresh_from_db()
        assert self.manufacturer.name == "AcmeCorp"
        assert self.manufacturer.description == ""
