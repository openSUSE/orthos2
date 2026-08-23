"""Tests for the ServerConfig Add/Edit/Delete API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import ServerConfig


class ServerConfigCommandTestCase(APITestCase):
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


class AddServerConfigTest(ServerConfigCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:serverconfig_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:serverconfig_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:serverconfig_add")
        response = self.client.post(
            url,
            {"form": {"key": "acme.test.key", "value": "acme-value"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not ServerConfig.objects.filter(key="acme.test.key").exists()

    def test_superuser_post_creates_serverconfig(self) -> None:
        self._auth_superuser()
        url = reverse("api:serverconfig_add")
        response = self.client.post(
            url,
            {"form": {"key": "acme.test.key", "value": "acme-value"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert ServerConfig.objects.filter(key="acme.test.key").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = ServerConfig.objects.count()
        url = reverse("api:serverconfig_add")
        response = self.client.post(url, {"form": {"key": ""}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert ServerConfig.objects.count() == count_before


class EditServerConfigTest(ServerConfigCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.serverconfig = ServerConfig.objects.create(
            key="acme.test.key", value="acme-value"
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:serverconfig_edit")
        response = self.client.get(url, {"id": self.serverconfig.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:serverconfig_edit")
        response = self.client.get(url, {"id": self.serverconfig.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:serverconfig_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:serverconfig_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.serverconfig.pk,
                    "key": "acme.test.key",
                    "value": "new-value",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.serverconfig.refresh_from_db()
        assert self.serverconfig.value == "acme-value"

    def test_superuser_post_updates_serverconfig(self) -> None:
        self._auth_superuser()
        url = reverse("api:serverconfig_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.serverconfig.pk,
                    "key": "acme.test.key",
                    "value": "new-value",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.serverconfig.refresh_from_db()
        assert self.serverconfig.value == "new-value"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:serverconfig_edit")
        response = self.client.post(
            url,
            {"form": {"id": 99999, "key": "acme.test.key", "value": "new-value"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteServerConfigTest(ServerConfigCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.serverconfig = ServerConfig.objects.create(
            key="acme.test.key", value="acme-value"
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:serverconfig_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:serverconfig_delete")
        response = self.client.post(
            url, {"form": {"key": "acme.test.key"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert ServerConfig.objects.filter(key="acme.test.key").exists()

    def test_superuser_post_deletes_serverconfig(self) -> None:
        self._auth_superuser()
        url = reverse("api:serverconfig_delete")
        response = self.client.post(
            url, {"form": {"key": "acme.test.key"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not ServerConfig.objects.filter(key="acme.test.key").exists()

    def test_superuser_post_nonexistent_key_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:serverconfig_delete")
        response = self.client.post(
            url, {"form": {"key": "nonexistent.key"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class ServerConfigListTest(ServerConfigCommandTestCase):
    """The pre-existing read-only ServerConfigCommand still lists entries."""

    def setUp(self) -> None:
        super().setUp()
        self.serverconfig = ServerConfig.objects.create(
            key="acme.test.key", value="acme-value"
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:serverconfig")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:serverconfig")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()

    def test_superuser_get_lists_entries(self) -> None:
        self._auth_superuser()
        url = reverse("api:serverconfig")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "acme.test.key" in [row["key"] for row in data["data"]]
