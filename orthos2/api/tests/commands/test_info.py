from django.contrib.auth.models import User
from django.urls import reverse  # type: ignore
from rest_framework import status
from rest_framework.test import APITestCase


class InfoTest(APITestCase):
    """
    Test all routes that are related to the info endpoint.
    """

    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/api/fixtures/serializers/machines.json",
    ]

    def setUp(self) -> None:
        self.user = User.objects.create_superuser(
            username="testuser", email="test@test.de", password="12345"
        )
        self.client.force_authenticate(user=self.user)

    def test_info_get_infinite_reservation(self) -> None:
        """
        Verify that retrieving a machine with an infinite reservation is possible.
        """
        # Arrange
        url = reverse("api:machine")
        url += "?fqdn=test.testing.suse.de"
        self.maxDiff = None

        # Act
        response = self.client.get(url, format="json")
        json_response = response.json()

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("data" in json_response)
        self.assertTrue("header" in json_response)
        self.assertTrue("type" in json_response["header"])
        self.assertEqual(json_response["header"]["type"], "INFO")
        self.assertIn(
            json_response["data"]["reserved_until"]["value"],
            ("9999-12-31T22:59:59.999999+01:00", "9999-12-31T23:59:59.999999+01:00"),
        )
