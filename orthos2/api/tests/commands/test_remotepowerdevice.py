"""Tests for the RemotePowerDevice Add/Edit/Delete API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import (
    Architecture,
    Domain,
    RemotePowerDevice,
    RemotePowerType,
    ServerConfig,
)


class RemotePowerDeviceCommandTestCase(APITestCase):
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

        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        self.domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        self.architecture = Architecture.objects.get(name="x86_64")
        self.fence_agent = RemotePowerType.objects.create(
            name="AcmeFenceAgent", device="rpowerdevice"
        )
        self.remotepowerdevice = RemotePowerDevice.objects.create(
            fqdn="rpower.orthos2.test",
            mac="AA:BB:CC:DD:EE:FF",
            fence_agent=self.fence_agent,
            architecture=self.architecture,
            domain=self.domain,
        )

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class EditRemotePowerDeviceTest(RemotePowerDeviceCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:remotepowerdevice_edit")
        response = self.client.get(url, {"id": self.remotepowerdevice.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowerdevice_edit")
        response = self.client.get(url, {"id": self.remotepowerdevice.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowerdevice_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:remotepowerdevice_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.remotepowerdevice.pk,
                    "fqdn": "rpower.orthos2.test",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "username": "newuser",
                    "password": "newpass",
                    "fence_agent": self.fence_agent.id,
                    "url": "",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.remotepowerdevice.refresh_from_db()
        assert self.remotepowerdevice.username != "newuser"

    def test_superuser_post_updates_remotepowerdevice(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowerdevice_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.remotepowerdevice.pk,
                    "fqdn": "rpower.orthos2.test",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "username": "newuser",
                    "password": "newpass",
                    "fence_agent": self.fence_agent.id,
                    "url": "",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.remotepowerdevice.refresh_from_db()
        assert self.remotepowerdevice.username == "newuser"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowerdevice_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": 99999,
                    "fqdn": "rpower.orthos2.test",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "username": "newuser",
                    "password": "newpass",
                    "fence_agent": self.fence_agent.id,
                    "url": "",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
