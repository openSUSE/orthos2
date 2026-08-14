"""
This test module verifies the functionality of "/<model>/add/".
"""
import json

from django.contrib.auth.models import User
from django.urls import reverse  # type: ignore
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import BMC, Machine, ServerConfig
from orthos2.data.models.remotepowertype import RemotePowerType


class AddBMCTest(APITestCase):
    """Test all routes that add instances of a BMC to the database."""

    fixtures = [
        "orthos2/api/fixtures/commands/add_bmc_post.json",
        "orthos2/data/fixtures/systems.json",
        "orthos2/data/fixtures/tests/test_machines.json",
    ]

    def setUp(self) -> None:
        self.user = User.objects.create_superuser(
            username="testuser", email="test@test.de", password="12345"
        )
        auth_token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + auth_token.key)

    def test_add_bmc_get(self) -> None:
        # Arrange
        url = reverse("api:bmc_add_get")
        url += "/test"
        data = {
            "fqdn": "test.testing.suse.de",
            "mac": "aa:bb:cc:dd:ee:ff",
            "username": "",
            "password": "",
            "fence_name": "",
        }

        # Act
        response = self.client.get(url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = json.loads(response.content)
        self.assertTrue(isinstance(json_response.get("header"), dict))
        self.assertEqual(json_response.get("header").get("type"), "INPUT")

    def test_add_bmc_post(self) -> None:
        """Test the route /bmc/add/{fqdn}"""
        # Arrange
        agent = RemotePowerType.objects.get(name="ipmilanplus")
        url = reverse("api:bmc_add_post", kwargs={"fqdn": "test.testing.suse.de"})
        data = {
            "form": {
                "fqdn": "test.testing.suse.de",
                "mac": "aa:bb:cc:dd:ee:ff",
                "username": "",
                "password": "",
                "fence_agent": agent.id,
            }
        }

        # Act
        response = self.client.post(url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BMC.objects.count(), 1)


class AddMachineTest(APITestCase):
    """Test the route /machine/add."""

    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/data/fixtures/tests/test_machines.json",
    ]

    def setUp(self) -> None:
        self.user = User.objects.create_superuser(
            username="testuser", email="test@test.de", password="12345"
        )
        auth_token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + auth_token.key)
        ServerConfig.objects.update_or_create(
            key="domain.validendings", defaults={"value": "our-org.tld"}
        )

    def test_add_machine_post(self) -> None:
        """
        A freshly constructed Machine has no primary key yet, so its primary
        network interface must be created and linked *after* Machine.save() -
        not before, and not left unattached (regression test for both).
        """
        # Arrange
        url = reverse("api:machine_add")
        data = {
            "form": {
                "fqdn": "new-machine.example.our-org.tld",
                "mac_address": "aa:bb:cc:dd:ee:02",
                "architecture_id": 1,
                "system_id": 1,
                "group_id": "none",
                "enclosure": "",
                "hypervisor_fqdn": "",
                "nda": False,
                "administrative": False,
                "check_connectivity": 0,
                "collect_system_information": False,
            }
        }

        # Act
        response = self.client.post(url, data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = json.loads(response.content)
        self.assertIsNone(json_response.get("data", {}).get("type"))
        machine = Machine.objects.get(fqdn="new-machine.example.our-org.tld")
        primary_interface = machine.networkinterfaces.get(primary=True)
        self.assertEqual(primary_interface.mac_address, "AA:BB:CC:DD:EE:02")
