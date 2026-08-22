"""Tests for the RemotePower Edit API command."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Machine, RemotePowerDevice, RemotePowerType


class RemotePowerCommandTestCase(APITestCase):
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

        # Machine pk=1 already has a remote power via RemotePowerDevice "apc" in the fixture.
        self.machine = Machine.objects.get(pk=1)
        self.remotepower = self.machine.remotepower
        self.remote_power_device = RemotePowerDevice.objects.get(
            fqdn="bmc.orthos2.test"
        )
        self.fence_agent = RemotePowerType.objects.get(name="apc")

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class EditRemotePowerTest(RemotePowerCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:remotepower_edit_get")
        response = self.client.get(url, {"fqdn": self.machine.fqdn})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepower_edit_get")
        response = self.client.get(url, {"fqdn": self.machine.fqdn})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_no_remotepower_returns_error(self) -> None:
        self.remotepower.delete()
        self._auth_superuser()
        url = reverse("api:remotepower_edit_get")
        response = self.client.get(url, {"fqdn": self.machine.fqdn})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:remotepower_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {
                "form": {
                    "remote_power_device": self.remote_power_device.pk,
                    "comment": "updated",
                    "options": "",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.remotepower.refresh_from_db()
        assert self.remotepower.comment != "updated"

    def test_superuser_post_updates_remotepower(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepower_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {
                "form": {
                    "remote_power_device": self.remote_power_device.pk,
                    "comment": "updated",
                    "options": "",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.remotepower.refresh_from_db()
        assert self.remotepower.comment == "updated"

    def test_superuser_post_no_remotepower_returns_error(self) -> None:
        self.remotepower.delete()
        self._auth_superuser()
        url = reverse("api:remotepower_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {
                "form": {
                    "remote_power_device": self.remote_power_device.pk,
                    "comment": "updated",
                    "options": "",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_superuser_post_invalid_port_returns_error(self) -> None:
        self.fence_agent.use_port = True
        self.fence_agent.save()

        self._auth_superuser()
        url = reverse("api:remotepower_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {
                "form": {
                    "remote_power_device": self.remote_power_device.pk,
                    "port": "not-a-number",
                    "options": "",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "port must be a number" in data["data"]["message"].lower()
        self.remotepower.refresh_from_db()
        assert self.remotepower.comment != "updated"
