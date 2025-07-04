"""
This test module verifies the functionality of "/<model>/add/".
"""
import json

from django.contrib.auth.models import User
from django.urls import reverse  # type: ignore
from rest_framework import status
from rest_framework.test import APITestCase

from orthos2.data.models import BMC
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
        self.client.force_authenticate(user=self.user)

    def test_add_bmc_get(self) -> None:
        # Arrange
        url = reverse("api:bmc_add")
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
        url = reverse("api:bmc_add")
        url += "/test%2Etesting%2Esuse%2Ede"
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
