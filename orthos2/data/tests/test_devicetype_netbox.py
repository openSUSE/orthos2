"""Tests for DeviceType.fetch_netbox() and DeviceType.compare_netbox()."""

from unittest.mock import patch

from django.test import TestCase

from orthos2.data.models import DeviceType, Manufacturer
from orthos2.data.models.netboxorthoscomparision import (
    NetboxOrthosComparisionResult,
    NetboxOrthosComparisionRun,
)

NETBOX_DEVICETYPE_RECORD = {
    "id": 42,
    "model": "PowerEdge R730",
    "description": "Updated by NetBox",
}


class FetchNetboxTest(TestCase):
    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=self.manufacturer, netbox_id=42
        )

    def test_skips_when_netbox_id_is_zero(self) -> None:
        devicetype = DeviceType.objects.create(
            name="NoNetbox", manufacturer=self.manufacturer, netbox_id=0
        )
        with patch.object(devicetype, "fetch_netbox_record") as mocked_fetch:
            devicetype.fetch_netbox()
        mocked_fetch.assert_not_called()

    def test_overwrites_name_and_description(self) -> None:
        with patch.object(
            self.devicetype,
            "fetch_netbox_record",
            return_value=NETBOX_DEVICETYPE_RECORD,
        ):
            self.devicetype.fetch_netbox()

        self.devicetype.refresh_from_db()
        assert self.devicetype.name == "PowerEdge R730"
        assert self.devicetype.description == "Updated by NetBox"
        assert self.devicetype.netbox_last_fetch_attempt is not None

    def test_stamps_fetch_attempt_even_when_record_not_found(self) -> None:
        with patch.object(self.devicetype, "fetch_netbox_record", return_value=None):
            self.devicetype.fetch_netbox()

        self.devicetype.refresh_from_db()
        assert self.devicetype.name == "AcmeDeviceType"
        assert self.devicetype.netbox_last_fetch_attempt is not None


class CompareNetboxTest(TestCase):
    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=self.manufacturer, netbox_id=42
        )

    def test_skips_when_netbox_id_is_zero(self) -> None:
        devicetype = DeviceType.objects.create(
            name="NoNetbox", manufacturer=self.manufacturer, netbox_id=0
        )
        devicetype.compare_netbox()
        assert NetboxOrthosComparisionRun.objects.count() == 0

    def test_creates_run_and_results(self) -> None:
        with patch.object(
            self.devicetype,
            "fetch_netbox_record",
            return_value=NETBOX_DEVICETYPE_RECORD,
        ):
            self.devicetype.compare_netbox()

        run = NetboxOrthosComparisionRun.objects.get(object_device_type=self.devicetype)
        assert (
            run.object_type
            == NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.DEVICE_TYPE
        )

        results = {
            result.property_name: result
            for result in NetboxOrthosComparisionResult.objects.filter(run_id=run)
        }
        assert results["name"].orthos_result == "AcmeDeviceType"
        assert results["name"].netbox_result == "PowerEdge R730"
        assert results["description"].orthos_result == "<not set>"
        assert results["description"].netbox_result == "Updated by NetBox"

        # compare_netbox must not mutate the devicetype itself
        self.devicetype.refresh_from_db()
        assert self.devicetype.name == "AcmeDeviceType"
        assert self.devicetype.description == ""
