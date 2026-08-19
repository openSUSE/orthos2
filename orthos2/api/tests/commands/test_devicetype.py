"""Tests for the DeviceType Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import DeviceType, Manufacturer


class DeviceTypeCommandTestCase(APITestCase):
    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(
            username="superuser", email="super@test.de", password="secret"
        )
        self.regular_user = User.objects.create_user(
            username="user", email="user@test.de", password="secret"
        )
        superuser_token, _ = Token.objects.get_or_create(user=self.superuser)
        self.superuser_token = superuser_token.key
        regular_token, _ = Token.objects.get_or_create(user=self.regular_user)
        self.regular_user_token = regular_token.key
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class AddDeviceTypeTest(DeviceTypeCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:devicetype_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:devicetype_add")
        response = self.client.post(
            url,
            {"form": {"name": "AcmeDeviceType", "manufacturer": self.manufacturer.pk}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not DeviceType.objects.filter(name="AcmeDeviceType").exists()

    def test_superuser_post_creates_devicetype(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype_add")
        response = self.client.post(
            url,
            {"form": {"name": "AcmeDeviceType", "manufacturer": self.manufacturer.pk}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert DeviceType.objects.filter(name="AcmeDeviceType").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = DeviceType.objects.count()
        url = reverse("api:devicetype_add")
        response = self.client.post(
            url,
            {"form": {"name": "", "manufacturer": self.manufacturer.pk}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert DeviceType.objects.count() == count_before


class EditDeviceTypeTest(DeviceTypeCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=self.manufacturer
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:devicetype_edit")
        response = self.client.get(url, {"id": self.devicetype.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype_edit")
        response = self.client.get(url, {"id": self.devicetype.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:devicetype_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.devicetype.pk,
                    "name": "AcmeDeviceType Renamed",
                    "manufacturer": self.manufacturer.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.devicetype.refresh_from_db()
        assert self.devicetype.name == "AcmeDeviceType"

    def test_superuser_post_updates_devicetype(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.devicetype.pk,
                    "name": "AcmeDeviceType Renamed",
                    "manufacturer": self.manufacturer.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.devicetype.refresh_from_db()
        assert self.devicetype.name == "AcmeDeviceType Renamed"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": 99999,
                    "name": "AcmeDeviceType Renamed",
                    "manufacturer": self.manufacturer.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteDeviceTypeTest(DeviceTypeCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=self.manufacturer
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:devicetype_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:devicetype_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeDeviceType"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert DeviceType.objects.filter(name="AcmeDeviceType").exists()

    def test_superuser_post_deletes_devicetype(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeDeviceType"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not DeviceType.objects.filter(name="AcmeDeviceType").exists()

    def test_superuser_post_nonexistent_name_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype_delete")
        response = self.client.post(
            url, {"form": {"name": "Nonexistent"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class DeviceTypeInfoTest(DeviceTypeCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=self.manufacturer
        )

    def test_get_single_devicetype_by_name(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype")
        response = self.client.get(url, {"name": "AcmeDeviceType"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmeDeviceType"

    def test_get_all_devicetypes_when_no_name_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "AcmeDeviceType" in [row["name"] for row in data["data"]]

    def test_get_nonexistent_devicetype_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:devicetype")
        response = self.client.get(url, {"name": "Nonexistent"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:devicetype")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:devicetype")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
