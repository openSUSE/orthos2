"""Tests for the BMC Edit/Delete API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import BMC, Machine, RemotePowerType


class BMCCommandTestCase(APITestCase):
    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

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

        self.fence_agent = RemotePowerType.objects.get(name="ipmilanplus")
        # Machine pk=1 (cobbler.orthos2.test) has a BMC ("my-bmc.foo.lan") in the fixture.
        self.machine = Machine.objects.get(pk=1)
        self.bmc = self.machine.bmc

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class EditBMCTest(BMCCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:bmc_edit")
        response = self.client.get(url, {"id": self.bmc.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:bmc_edit")
        response = self.client.get(url, {"id": self.bmc.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_no_bmc_returns_error(self) -> None:
        url = reverse("api:bmc_edit")
        self._auth_superuser()
        response = self.client.get(url, {"id": 9999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:bmc_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.bmc.pk,
                    "fqdn": self.bmc.fqdn,
                    "mac": "AA:BB:CC:DD:EE:05",
                    "username": "",
                    "password": "",
                    "fence_agent": self.fence_agent.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.bmc.refresh_from_db()
        assert self.bmc.mac != "AA:BB:CC:DD:EE:05"

    def test_superuser_post_updates_bmc(self) -> None:
        self._auth_superuser()
        url = reverse("api:bmc_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.bmc.pk,
                    "fqdn": self.bmc.fqdn,
                    "mac": "AA:BB:CC:DD:EE:05",
                    "username": "",
                    "password": "",
                    "fence_agent": self.fence_agent.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.bmc.refresh_from_db()
        assert self.bmc.mac == "AA:BB:CC:DD:EE:05"

    def test_superuser_post_no_bmc_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:bmc_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": 9999,
                    "fqdn": self.bmc.fqdn,
                    "mac": "AA:BB:CC:DD:EE:05",
                    "username": "",
                    "password": "",
                    "fence_agent": self.fence_agent.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_superuser_post_username_without_password_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:bmc_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.bmc.pk,
                    "fqdn": self.bmc.fqdn,
                    "mac": "AA:BB:CC:DD:EE:05",
                    "username": "root",
                    "password": "",
                    "fence_agent": self.fence_agent.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        self.bmc.refresh_from_db()
        assert self.bmc.mac != "AA:BB:CC:DD:EE:05"


class DeleteBMCTest(BMCCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:bmc_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:bmc_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:bmc_delete")
        response = self.client.post(
            url, {"form": {"fqdn": self.bmc.fqdn}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert BMC.objects.filter(pk=self.bmc.pk).exists()

    def test_superuser_post_deletes_bmc(self) -> None:
        self._auth_superuser()
        url = reverse("api:bmc_delete")
        response = self.client.post(
            url, {"form": {"fqdn": self.bmc.fqdn}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not BMC.objects.filter(pk=self.bmc.pk).exists()

    def test_superuser_post_unknown_fqdn_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:bmc_delete")
        response = self.client.post(
            url, {"form": {"fqdn": "does-not-exist.orthos2.test"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
