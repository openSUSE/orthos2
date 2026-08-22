"""Tests for Manufacturer.get_or_create_from_netbox()."""

from unittest.mock import patch

from django.test import TestCase
from requests import HTTPError
from requests.models import Response

from orthos2.data.models import Manufacturer

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
    Migration 0044_initial_required_data.py seeds 28 Manufacturer rows with
    netbox_id=0, including one named "AMD" - the exact NetBox manufacturer
    name used here, so the name-fallback/backfill path is exercised against
    real seed data rather than an artificial collision.
    """

    def test_returns_none_for_falsy_id(self) -> None:
        assert Manufacturer.get_or_create_from_netbox(0) is None
        assert Manufacturer.get_or_create_from_netbox(None) is None

    def test_creates_manufacturer_when_none_exists(self) -> None:
        record = {**NETBOX_MANUFACTURER_RECORD, "id": 99, "name": "AcmeCorp"}
        with patch("orthos2.data.models.manufacturer.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_manufacturer.return_value = (
                record
            )
            manufacturer = Manufacturer.get_or_create_from_netbox(99)

        assert manufacturer is not None
        assert manufacturer.name == "AcmeCorp"
        assert manufacturer.netbox_id == 99

    def test_reuses_manufacturer_already_linked_by_netbox_id_without_refetching(
        self,
    ) -> None:
        existing = Manufacturer.objects.create(
            name="AMD (renamed locally)", netbox_id=4
        )
        with patch("orthos2.data.models.manufacturer.Netbox") as mocked_netbox_cls:
            manufacturer = Manufacturer.get_or_create_from_netbox(4)

        assert manufacturer is not None
        assert manufacturer.pk == existing.pk
        mocked_netbox_cls.get_instance.return_value.fetch_manufacturer.assert_not_called()

    def test_links_existing_unlinked_manufacturer_found_by_name(self) -> None:
        # Seeded by migration 0044_initial_required_data.py, netbox_id=0.
        existing_amd = Manufacturer.objects.get(name="AMD")
        assert existing_amd.netbox_id == 0

        with patch("orthos2.data.models.manufacturer.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_manufacturer.return_value = (
                NETBOX_MANUFACTURER_RECORD
            )
            manufacturer = Manufacturer.get_or_create_from_netbox(4)

        existing_amd.refresh_from_db()
        assert existing_amd.netbox_id == 4
        assert manufacturer is not None
        assert manufacturer.pk == existing_amd.pk
        assert Manufacturer.objects.filter(name="AMD").count() == 1

    def test_returns_none_on_404(self) -> None:
        with patch("orthos2.data.models.manufacturer.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_manufacturer.side_effect = _http_error(
                404
            )
            manufacturer = Manufacturer.get_or_create_from_netbox(999)

        assert manufacturer is None
        assert not Manufacturer.objects.filter(netbox_id=999).exists()

    def test_reraises_non_404_http_error(self) -> None:
        with patch("orthos2.data.models.manufacturer.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_manufacturer.side_effect = _http_error(
                500
            )
            with self.assertRaises(HTTPError):
                Manufacturer.get_or_create_from_netbox(4)

    def test_returns_none_when_name_missing(self) -> None:
        record = {**NETBOX_MANUFACTURER_RECORD, "name": None}
        with patch("orthos2.data.models.manufacturer.Netbox") as mocked_netbox_cls:
            mocked_netbox_cls.get_instance.return_value.fetch_manufacturer.return_value = (
                record
            )
            manufacturer = Manufacturer.get_or_create_from_netbox(4)

        assert manufacturer is None
        assert not Manufacturer.objects.filter(netbox_id=4).exists()
