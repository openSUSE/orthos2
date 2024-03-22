"""
This test module verifies the functionality of "/<model>/add/".
"""
import json

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orthos2.data.models import BMC


class AddBMCTest(APITestCase):
    """Test all routes that add instances of a BMC to the database."""

    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/data/fixtures/vendors.json",
        "orthos2/data/fixtures/tests/test_machines.json"
    ]

    remote_power_types = [
        {
            'fence': 'ipmilanplus',
            'device': 'bmc',
            'username': 'xxx',
            'password': 'XXX',
            'arch': ['x86_64', 'aarch64'],
            'system': ['Bare Metal']
        },
    ]

    def setUp(self) -> None:
        self.user = User.objects.create_superuser(username='testuser', email="test@test.de", password='12345')
        self.client.force_authenticate(user=self.user)

    def test_add_bmc_get(self):
        # Arrange
        url = reverse('api:bmc_add')
        url += "/test"
        data = {'fqdn': 'test.testing.suse.de', 'mac': 'DabApps', 'username': '', 'password': '', 'fence_name': ''}

        # Act
        response = self.client.get(url, data, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = json.loads(response.content)
        self.assertTrue(isinstance(json_response.get("header"), dict))
        self.assertEqual(json_response.get("header").get("type"), "INPUT")

    @override_settings(REMOTEPOWER_TYPES=remote_power_types)
    def test_add_bmc_post(self):
        """Test the route /bmc/add/{fqdn}"""
        # Arrange
        url = reverse('api:bmc_add')
        url += "/test%2Etesting%2Esuse%2Ede"
        data = {
            "form": {
                'fqdn': 'test.testing.suse.de',
                'mac': 'DabApps',
                'username': '',
                'password': '',
                'fence_name': 'ipmilanplus'
            }
        }

        # Act
        response = self.client.post(url, data, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BMC.objects.count(), 1)
