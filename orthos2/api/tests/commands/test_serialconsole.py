"""Tests for the SerialConsole Edit API command."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Machine, SerialConsole, SerialConsoleType


class SerialConsoleCommandTestCase(APITestCase):
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

        # "Device" type has no BMC dependency, unlike the fixture's "IPMI" type.
        self.device_type = SerialConsoleType.objects.create(
            name="Device", command="", comment="", has_ipmi_sol=False
        )
        self.machine = Machine.objects.get(pk=1)
        self.serialconsole = SerialConsole.objects.create(
            machine=self.machine,
            stype=self.device_type,
            baud_rate=57600,
            kernel_device="ttyS",
            kernel_device_num=0,
        )

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class EditSerialConsoleTest(SerialConsoleCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:serialconsole_edit_get")
        response = self.client.get(url, {"fqdn": self.machine.fqdn})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsole_edit_get")
        response = self.client.get(url, {"fqdn": self.machine.fqdn})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_no_serialconsole_returns_error(self) -> None:
        self.serialconsole.delete()
        self._auth_superuser()
        url = reverse("api:serialconsole_edit_get")
        response = self.client.get(url, {"fqdn": self.machine.fqdn})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:serialconsole_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {
                "form": {
                    "stype": self.device_type.pk,
                    "baud_rate": 115200,
                    "kernel_device": "ttyS",
                    "kernel_device_num": 0,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.serialconsole.refresh_from_db()
        assert self.serialconsole.baud_rate == 57600

    def test_superuser_post_updates_serialconsole(self) -> None:
        self._auth_superuser()
        url = reverse("api:serialconsole_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {
                "form": {
                    "stype": self.device_type.pk,
                    "baud_rate": 115200,
                    "kernel_device": "ttyS",
                    "kernel_device_num": 0,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.serialconsole.refresh_from_db()
        assert self.serialconsole.baud_rate == 115200

    def test_superuser_post_no_serialconsole_returns_error(self) -> None:
        self.serialconsole.delete()
        self._auth_superuser()
        url = reverse("api:serialconsole_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {
                "form": {
                    "stype": self.device_type.pk,
                    "baud_rate": 115200,
                    "kernel_device": "ttyS",
                    "kernel_device_num": 0,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
