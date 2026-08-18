"""Tests for the System Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import System


class SystemCommandTestCase(APITestCase):
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


class AddSystemTest(SystemCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:system_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:system_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:system_add")
        response = self.client.post(
            url, {"form": {"name": "AcmeSystem"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not System.objects.filter(name="AcmeSystem").exists()

    def test_superuser_post_creates_system(self) -> None:
        self._auth_superuser()
        url = reverse("api:system_add")
        response = self.client.post(
            url, {"form": {"name": "AcmeSystem"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert System.objects.filter(name="AcmeSystem").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = System.objects.count()
        url = reverse("api:system_add")
        response = self.client.post(url, {"form": {"name": ""}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert System.objects.count() == count_before


class EditSystemTest(SystemCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.system = System.objects.create(name="AcmeSystem")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:system_edit")
        response = self.client.get(url, {"id": self.system.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:system_edit")
        response = self.client.get(url, {"id": self.system.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:system_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:system_edit")
        response = self.client.post(
            url,
            {"form": {"id": self.system.pk, "name": "AcmeSystem Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.system.refresh_from_db()
        assert self.system.name == "AcmeSystem"

    def test_superuser_post_updates_system(self) -> None:
        self._auth_superuser()
        url = reverse("api:system_edit")
        response = self.client.post(
            url,
            {"form": {"id": self.system.pk, "name": "AcmeSystem Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.system.refresh_from_db()
        assert self.system.name == "AcmeSystem Renamed"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:system_edit")
        response = self.client.post(
            url,
            {"form": {"id": 99999, "name": "AcmeSystem Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteSystemTest(SystemCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.system = System.objects.create(name="AcmeSystem")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:system_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:system_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeSystem"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert System.objects.filter(name="AcmeSystem").exists()

    def test_superuser_post_deletes_system(self) -> None:
        self._auth_superuser()
        url = reverse("api:system_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeSystem"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not System.objects.filter(name="AcmeSystem").exists()

    def test_superuser_post_nonexistent_name_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:system_delete")
        response = self.client.post(
            url, {"form": {"name": "Nonexistent"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class SystemInfoTest(SystemCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.system = System.objects.create(name="AcmeSystem")

    def test_get_single_system_by_name(self) -> None:
        self._auth_superuser()
        url = reverse("api:system")
        response = self.client.get(url, {"name": "AcmeSystem"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmeSystem"

    def test_get_all_systems_when_no_name_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:system")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "AcmeSystem" in [row["name"] for row in data["data"]]

    def test_get_nonexistent_system_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:system")
        response = self.client.get(url, {"name": "Nonexistent"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:system")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:system")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
