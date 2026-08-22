"""Tests for the SerialConsoleType Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import SerialConsoleType


class SerialConsoleTypeCommandTestCase(APITestCase):
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


class AddSerialConsoleTypeTest(SerialConsoleTypeCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:serialconsoletype_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:serialconsoletype_add")
        response = self.client.post(
            url, {"form": {"name": "AcmeConsole"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not SerialConsoleType.objects.filter(name="AcmeConsole").exists()

    def test_superuser_post_creates_serialconsoletype(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype_add")
        response = self.client.post(
            url, {"form": {"name": "AcmeConsole"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert SerialConsoleType.objects.filter(name="AcmeConsole").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = SerialConsoleType.objects.count()
        url = reverse("api:serialconsoletype_add")
        response = self.client.post(url, {"form": {"name": ""}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert SerialConsoleType.objects.count() == count_before


class EditSerialConsoleTypeTest(SerialConsoleTypeCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.serialconsoletype = SerialConsoleType.objects.create(name="AcmeConsole")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:serialconsoletype_edit")
        response = self.client.get(url, {"id": self.serialconsoletype.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype_edit")
        response = self.client.get(url, {"id": self.serialconsoletype.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:serialconsoletype_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.serialconsoletype.pk,
                    "name": "AcmeConsole Renamed",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.serialconsoletype.refresh_from_db()
        assert self.serialconsoletype.name == "AcmeConsole"

    def test_superuser_post_updates_serialconsoletype(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.serialconsoletype.pk,
                    "name": "AcmeConsole Renamed",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.serialconsoletype.refresh_from_db()
        assert self.serialconsoletype.name == "AcmeConsole Renamed"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype_edit")
        response = self.client.post(
            url,
            {"form": {"id": 99999, "name": "AcmeConsole Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteSerialConsoleTypeTest(SerialConsoleTypeCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.serialconsoletype = SerialConsoleType.objects.create(name="AcmeConsole")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:serialconsoletype_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:serialconsoletype_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeConsole"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert SerialConsoleType.objects.filter(name="AcmeConsole").exists()

    def test_superuser_post_deletes_serialconsoletype(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeConsole"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not SerialConsoleType.objects.filter(name="AcmeConsole").exists()

    def test_superuser_post_nonexistent_name_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype_delete")
        response = self.client.post(
            url, {"form": {"name": "Nonexistent"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class SerialConsoleTypeInfoTest(SerialConsoleTypeCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.serialconsoletype = SerialConsoleType.objects.create(name="AcmeConsole")

    def test_get_single_serialconsoletype_by_name(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype")
        response = self.client.get(url, {"name": "AcmeConsole"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmeConsole"

    def test_get_all_serialconsoletypes_when_no_name_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "AcmeConsole" in [row["name"] for row in data["data"]]

    def test_get_nonexistent_serialconsoletype_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsoletype")
        response = self.client.get(url, {"name": "Nonexistent"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:serialconsoletype")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:serialconsoletype")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
