"""Tests for the Enclosure Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Enclosure


class EnclosureCommandTestCase(APITestCase):
    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(
            username="superuser", email="super@orthos2.test", password="secret"
        )
        self.regular_user = User.objects.create_user(
            username="user", email="user@orthos2.test", password="secret"
        )
        superuser_token, _ = Token.objects.get_or_create(user=self.superuser)
        self.superuser_token = superuser_token.key
        regular_token, _ = Token.objects.get_or_create(user=self.regular_user)
        self.regular_user_token = regular_token.key

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class AddEnclosureTest(EnclosureCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:enclosure_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:enclosure_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:enclosure_add")
        response = self.client.post(
            url, {"form": {"name": "AcmeEnclosure"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not Enclosure.objects.filter(name="AcmeEnclosure").exists()

    def test_superuser_post_creates_enclosure(self) -> None:
        self._auth_superuser()
        url = reverse("api:enclosure_add")
        response = self.client.post(
            url,
            {"form": {"name": "AcmeEnclosure", "netbox_id": 0}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert Enclosure.objects.filter(name="AcmeEnclosure").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = Enclosure.objects.count()
        url = reverse("api:enclosure_add")
        response = self.client.post(url, {"form": {"name": ""}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert Enclosure.objects.count() == count_before


class EditEnclosureTest(EnclosureCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.enclosure = Enclosure.objects.create(name="AcmeEnclosure")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:enclosure_edit")
        response = self.client.get(url, {"id": self.enclosure.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:enclosure_edit")
        response = self.client.get(url, {"id": self.enclosure.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:enclosure_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:enclosure_edit")
        response = self.client.post(
            url,
            {"form": {"id": self.enclosure.pk, "name": "AcmeEnclosure Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.enclosure.refresh_from_db()
        assert self.enclosure.name == "AcmeEnclosure"

    def test_superuser_post_updates_enclosure(self) -> None:
        self._auth_superuser()
        url = reverse("api:enclosure_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.enclosure.pk,
                    "name": "AcmeEnclosure Renamed",
                    "netbox_id": 0,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.enclosure.refresh_from_db()
        assert self.enclosure.name == "AcmeEnclosure Renamed"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:enclosure_edit")
        response = self.client.post(
            url,
            {"form": {"id": 99999, "name": "AcmeEnclosure Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteEnclosureTest(EnclosureCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.enclosure = Enclosure.objects.create(name="AcmeEnclosure")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:enclosure_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:enclosure_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeEnclosure"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert Enclosure.objects.filter(name="AcmeEnclosure").exists()

    def test_superuser_post_deletes_enclosure(self) -> None:
        self._auth_superuser()
        url = reverse("api:enclosure_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeEnclosure"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not Enclosure.objects.filter(name="AcmeEnclosure").exists()

    def test_superuser_post_nonexistent_name_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:enclosure_delete")
        response = self.client.post(
            url, {"form": {"name": "Nonexistent"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class EnclosureInfoTest(EnclosureCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.enclosure = Enclosure.objects.create(name="AcmeEnclosure")

    def test_get_single_enclosure_by_name(self) -> None:
        self._auth_superuser()
        url = reverse("api:enclosure")
        response = self.client.get(url, {"name": "AcmeEnclosure"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmeEnclosure"
