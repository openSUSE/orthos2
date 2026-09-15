"""Tests for device_type resolution in Enclosure.fetch_netbox()/compare_netbox()."""

from unittest.mock import patch

from django.test import TestCase

from orthos2.data.models import DeviceType, Enclosure, Manufacturer
from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionResult

NETBOX_ENCLOSURE_RECORD = {
    "description": "",
    "site": {},
    "location": None,
    "rack": None,
    "position": None,
    "device_type": {
        "id": 6,
        "manufacturer": {"id": 4, "name": "AMD"},
        "model": "EPYC ROME",
        "display": "EPYC ROME",
    },
}

NETBOX_ENCLOSURE_RECORD_NO_DEVICE_TYPE = {
    "description": "",
    "site": {},
    "location": None,
    "rack": None,
    "position": None,
    "device_type": None,
}


class FetchNetboxDeviceTypeTest(TestCase):
    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AMD-Local", netbox_id=4)
        self.device_type = DeviceType.objects.create(
            name="EPYC ROME", manufacturer=self.manufacturer, netbox_id=6
        )
        self.enclosure = Enclosure.objects.create(name="test-enclosure", netbox_id=42)

    def _fetch_netbox(self, netbox_record) -> None:
        with patch.object(
            self.enclosure, "fetch_netbox_record", return_value=netbox_record
        ), patch(
            "orthos2.data.models.enclosure.DeviceType.get_or_create_from_netbox"
        ) as mocked_resolver:
            mocked_resolver.return_value = self.device_type
            self.enclosure.fetch_netbox()
        self._mocked_resolver = mocked_resolver

    def test_resolves_device_type_when_unset(self) -> None:
        self._fetch_netbox(NETBOX_ENCLOSURE_RECORD)

        self._mocked_resolver.assert_called_once_with(6)
        self.enclosure.refresh_from_db()
        assert self.enclosure.device_type_id == self.device_type.pk

    def test_skips_resolution_for_record_without_device_type(self) -> None:
        self._fetch_netbox(NETBOX_ENCLOSURE_RECORD_NO_DEVICE_TYPE)

        self._mocked_resolver.assert_not_called()
        self.enclosure.refresh_from_db()
        assert self.enclosure.device_type is None


class CompareNetboxDeviceTypeTest(TestCase):
    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AMD-Local", netbox_id=4)
        self.device_type = DeviceType.objects.create(
            name="EPYC ROME", manufacturer=self.manufacturer, netbox_id=6
        )
        self.enclosure = Enclosure.objects.create(
            name="test-enclosure", netbox_id=42, device_type=self.device_type
        )

    def test_creates_device_type_comparison_result(self) -> None:
        with patch.object(
            self.enclosure,
            "fetch_netbox_record",
            return_value=NETBOX_ENCLOSURE_RECORD,
        ):
            self.enclosure.compare_netbox()

        result = NetboxOrthosComparisionResult.objects.get(
            run_id__object_enclosure=self.enclosure, property_name="device_type"
        )
        assert result.orthos_result == str(self.device_type)
        assert result.netbox_result == "EPYC ROME"

    def test_missing_device_type_in_netbox_yields_not_set(self) -> None:
        with patch.object(
            self.enclosure,
            "fetch_netbox_record",
            return_value=NETBOX_ENCLOSURE_RECORD_NO_DEVICE_TYPE,
        ):
            self.enclosure.compare_netbox()

        result = NetboxOrthosComparisionResult.objects.get(
            run_id__object_enclosure=self.enclosure, property_name="device_type"
        )
        assert result.netbox_result == "<not set>"
