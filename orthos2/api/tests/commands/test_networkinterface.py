"""Tests for the NetworkInterface Add/Edit API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import BMC, NetworkInterface


class NetworkInterfaceCommandTestCase(APITestCase):
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

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class AddNetworkInterfaceTest(NetworkInterfaceCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:networkinterface_add_get")
        response = self.client.get(url, {"fqdn": "cobbler.orthos2.test"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:networkinterface_add_get")
        response = self.client.get(url, {"fqdn": "cobbler.orthos2.test"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse(
            "api:networkinterface_add_post", kwargs={"fqdn": "cobbler.orthos2.test"}
        )
        response = self.client.post(
            url,
            {
                "form": {
                    "mac_address": "AA:BB:CC:DD:EE:AA",
                    "ip_address_v4": "127.0.0.50",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not NetworkInterface.objects.filter(
            mac_address="AA:BB:CC:DD:EE:AA"
        ).exists()

    def test_superuser_post_creates_networkinterface(self) -> None:
        self._auth_superuser()
        url = reverse(
            "api:networkinterface_add_post", kwargs={"fqdn": "cobbler.orthos2.test"}
        )
        response = self.client.post(
            url,
            {
                "form": {
                    "mac_address": "AA:BB:CC:DD:EE:AA",
                    "ip_address_v4": "127.0.0.50",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert NetworkInterface.objects.filter(
            machine__fqdn="cobbler.orthos2.test", mac_address="AA:BB:CC:DD:EE:AA"
        ).exists()

    def test_superuser_post_second_primary_returns_error(self) -> None:
        # Machine cobbler.orthos2.test (pk=1) already has a primary interface.
        self._auth_superuser()
        url = reverse(
            "api:networkinterface_add_post", kwargs={"fqdn": "cobbler.orthos2.test"}
        )
        response = self.client.post(
            url,
            {
                "form": {
                    "primary": True,
                    "mac_address": "AA:BB:CC:DD:EE:AB",
                    "ip_address_v4": "127.0.0.51",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert not NetworkInterface.objects.filter(
            mac_address="AA:BB:CC:DD:EE:AB"
        ).exists()

    def test_superuser_post_mac_used_by_bmc_returns_error(self) -> None:
        bmc_mac = BMC.objects.get(pk=1).mac
        self._auth_superuser()
        url = reverse(
            "api:networkinterface_add_post", kwargs={"fqdn": "cobbler.orthos2.test"}
        )
        response = self.client.post(
            url,
            {"form": {"mac_address": bmc_mac, "ip_address_v4": "127.0.0.52"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert not NetworkInterface.objects.filter(
            machine__fqdn="cobbler.orthos2.test", mac_address=bmc_mac
        ).exists()


class EditNetworkInterfaceTest(NetworkInterfaceCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:networkinterface_edit")
        response = self.client.get(url, {"id": 3})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:networkinterface_edit")
        response = self.client.get(url, {"id": 3})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:networkinterface_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:networkinterface_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": 3,
                    "mac_address": "CA:FE:BE:EF:C0:DE",
                    "ip_address_v4": "127.0.0.60",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        interface = NetworkInterface.objects.get(pk=3)
        assert interface.ip_address_v4 == "127.0.0.11"

    def test_superuser_post_updates_networkinterface(self) -> None:
        self._auth_superuser()
        url = reverse("api:networkinterface_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": 3,
                    "mac_address": "CA:FE:BE:EF:C0:DE",
                    "ip_address_v4": "127.0.0.60",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        interface = NetworkInterface.objects.get(pk=3)
        assert interface.ip_address_v4 == "127.0.0.60"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:networkinterface_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": 99999,
                    "mac_address": "CA:FE:BE:EF:C0:DE",
                    "ip_address_v4": "127.0.0.60",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
