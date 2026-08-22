"""Tests for DeviceType.get_or_create_from_netbox()."""

from unittest.mock import patch

from django.test import TestCase
from requests import HTTPError
from requests.models import Response

from orthos2.data.models import DeviceType, Manufacturer

NETBOX_DEVICETYPE_RECORD = {
    "id": 6,
    "model": "EPYC ROME",
    "slug": "epyc-rome",
    "description": "",
    "manufacturer": {
        "id": 4,
        "name": "AMD",
        "slug": "amd",
    },
}

NETBOX_MANUFACTURER_RECORD = {
    "id": 4,
    "name": "AMD",
    "slug": "amd",
    "description": "",
}


def _http_error(status_code: int) -> HTTPError:
    response = Response()
    response.status_code = status_code
    return HTTPError(response=response)


class GetOrCreateFromNetboxTest(TestCase):
    """
    Manufacturer resolution is delegated to
    `Manufacturer.get_or_create_from_netbox()`, which calls NetBox via its
    own module-level `Netbox` reference (`orthos2.data.models.manufacturer`)
    - separate from DeviceType's (`orthos2.data.models.devicetype`). Most
    scenarios here never reach that call at all (an existing DeviceType or
    Manufacturer already linked by netbox_id short-circuits first), so only
    the two "resolve something brand new" tests need to mock both.
    """

    def test_returns_none_for_falsy_id(self) -> None:
        assert DeviceType.get_or_create_from_netbox(0) is None
        assert DeviceType.get_or_create_from_netbox(None) is None

    def test_creates_manufacturer_and_devicetype_when_neither_exists(self) -> None:
        record = {
            **NETBOX_DEVICETYPE_RECORD,
            "manufacturer": {"id": 99, "name": "AcmeCorp", "slug": "acmecorp"},
        }
        with patch(
            "orthos2.data.models.devicetype.Netbox"
        ) as mocked_devicetype_netbox_cls, patch(
            "orthos2.data.models.manufacturer.Netbox"
        ) as mocked_manufacturer_netbox_cls:
            mocked_devicetype_netbox_cls.get_instance.return_value.fetch_device_type.return_value = (
                record
            )
            mocked_manufacturer_netbox_cls.get_instance.return_value.fetch_manufacturer.return_value = {
                "id": 99,
                "name": "AcmeCorp",
            }
            device_type = DeviceType.get_or_create_from_netbox(6)

        assert device_type is not None
        assert device_type.name == "EPYC ROME"
        assert device_type.netbox_id == 6
        manufacturer = Manufacturer.objects.get(name="AcmeCorp")
        assert device_type.manufacturer_id == manufacturer.pk
        assert manufacturer.netbox_id == 99

    def test_reuses_manufacturer_already_linked_by_netbox_id(self) -> None:
        existing = Manufacturer.objects.create(
            name="AMD (renamed locally)", netbox_id=4
        )
        with patch("orthos2.data.models.devicetype.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_device_type.return_value = (
                NETBOX_DEVICETYPE_RECORD
            )
            device_type = DeviceType.get_or_create_from_netbox(6)

        assert device_type is not None
        assert device_type.manufacturer_id == existing.pk
        assert Manufacturer.objects.filter(netbox_id=4).count() == 1

    def test_links_existing_unlinked_manufacturer_found_by_name(self) -> None:
        # Seeded by migration 0044_initial_required_data.py, netbox_id=0.
        existing_amd = Manufacturer.objects.get(name="AMD")
        assert existing_amd.netbox_id == 0

        with patch(
            "orthos2.data.models.devicetype.Netbox"
        ) as mocked_devicetype_netbox_cls, patch(
            "orthos2.data.models.manufacturer.Netbox"
        ) as mocked_manufacturer_netbox_cls:
            mocked_devicetype_netbox_cls.get_instance.return_value.fetch_device_type.return_value = (
                NETBOX_DEVICETYPE_RECORD
            )
            mocked_manufacturer_netbox_cls.get_instance.return_value.fetch_manufacturer.return_value = (
                NETBOX_MANUFACTURER_RECORD
            )
            device_type = DeviceType.get_or_create_from_netbox(6)

        existing_amd.refresh_from_db()
        assert existing_amd.netbox_id == 4
        assert device_type is not None
        assert device_type.manufacturer_id == existing_amd.pk
        assert Manufacturer.objects.filter(name="AMD").count() == 1

    def test_reuses_devicetype_already_linked_by_netbox_id_without_refetching(
        self,
    ) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp", netbox_id=4)
        existing = DeviceType.objects.create(
            name="EPYC ROME (renamed locally)",
            manufacturer=manufacturer,
            netbox_id=6,
        )
        with patch("orthos2.data.models.devicetype.Netbox") as mocked_netbox_cls:
            device_type = DeviceType.get_or_create_from_netbox(6)

        assert device_type is not None
        assert device_type.pk == existing.pk
        assert device_type.name == "EPYC ROME (renamed locally)"
        mocked_netbox_cls.get_instance.return_value.fetch_device_type.assert_not_called()

    def test_links_existing_unlinked_devicetype_found_by_name_and_manufacturer(
        self,
    ) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp", netbox_id=4)
        existing = DeviceType.objects.create(
            name="EPYC ROME", manufacturer=manufacturer
        )
        record = {
            **NETBOX_DEVICETYPE_RECORD,
            "manufacturer": {"id": 4, "name": "AcmeCorp"},
        }
        with patch("orthos2.data.models.devicetype.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_device_type.return_value = (
                record
            )
            device_type = DeviceType.get_or_create_from_netbox(6)

        existing.refresh_from_db()
        assert existing.netbox_id == 6
        assert device_type is not None
        assert device_type.pk == existing.pk
        assert (
            DeviceType.objects.filter(
                manufacturer=manufacturer, name="EPYC ROME"
            ).count()
            == 1
        )

    def test_returns_none_on_404(self) -> None:
        with patch("orthos2.data.models.devicetype.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_device_type.side_effect = _http_error(
                404
            )
            device_type = DeviceType.get_or_create_from_netbox(999)

        assert device_type is None
        assert not DeviceType.objects.filter(netbox_id=999).exists()

    def test_reraises_non_404_http_error(self) -> None:
        with patch("orthos2.data.models.devicetype.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_device_type.side_effect = _http_error(
                500
            )
            with self.assertRaises(HTTPError):
                DeviceType.get_or_create_from_netbox(6)

    def test_returns_none_when_manufacturer_data_missing(self) -> None:
        record = {**NETBOX_DEVICETYPE_RECORD, "manufacturer": None}
        with patch("orthos2.data.models.devicetype.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_device_type.return_value = (
                record
            )
            device_type = DeviceType.get_or_create_from_netbox(6)

        assert device_type is None
        assert not DeviceType.objects.filter(netbox_id=6).exists()
