"""Tests for the Manufacturer Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Manufacturer


class ManufacturerCommandTestCase(APITestCase):
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

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class AddManufacturerTest(ManufacturerCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:manufacturer_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:manufacturer_add")
        response = self.client.post(url, {"form": {"name": "AcmeCorp"}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not Manufacturer.objects.filter(name="AcmeCorp").exists()

    def test_superuser_post_creates_manufacturer(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer_add")
        response = self.client.post(url, {"form": {"name": "AcmeCorp"}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert Manufacturer.objects.filter(name="AcmeCorp").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = Manufacturer.objects.count()
        url = reverse("api:manufacturer_add")
        response = self.client.post(url, {"form": {"name": ""}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert Manufacturer.objects.count() == count_before


class EditManufacturerTest(ManufacturerCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:manufacturer_edit")
        response = self.client.get(url, {"id": self.manufacturer.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer_edit")
        response = self.client.get(url, {"id": self.manufacturer.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:manufacturer_edit")
        response = self.client.post(
            url,
            {"form": {"id": self.manufacturer.pk, "name": "AcmeCorp Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.manufacturer.refresh_from_db()
        assert self.manufacturer.name == "AcmeCorp"

    def test_superuser_post_updates_manufacturer(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer_edit")
        response = self.client.post(
            url,
            {"form": {"id": self.manufacturer.pk, "name": "AcmeCorp Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.manufacturer.refresh_from_db()
        assert self.manufacturer.name == "AcmeCorp Renamed"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer_edit")
        response = self.client.post(
            url, {"form": {"id": 99999, "name": "AcmeCorp Renamed"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteManufacturerTest(ManufacturerCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:manufacturer_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:manufacturer_delete")
        response = self.client.post(url, {"form": {"name": "AcmeCorp"}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert Manufacturer.objects.filter(name="AcmeCorp").exists()

    def test_superuser_post_deletes_manufacturer(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer_delete")
        response = self.client.post(url, {"form": {"name": "AcmeCorp"}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not Manufacturer.objects.filter(name="AcmeCorp").exists()

    def test_superuser_post_nonexistent_name_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer_delete")
        response = self.client.post(
            url, {"form": {"name": "Nonexistent"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class ManufacturerInfoTest(ManufacturerCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_get_single_manufacturer_by_name(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer")
        response = self.client.get(url, {"name": "AcmeCorp"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmeCorp"

    def test_get_all_manufacturers_when_no_name_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "AcmeCorp" in [row["name"] for row in data["data"]]

    def test_get_nonexistent_manufacturer_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:manufacturer")
        response = self.client.get(url, {"name": "Nonexistent"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:manufacturer")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:manufacturer")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
