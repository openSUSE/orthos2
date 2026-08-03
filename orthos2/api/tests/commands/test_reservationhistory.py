import datetime

from django.contrib.auth.models import User
from django.urls import reverse  # type: ignore
from rest_framework import status
from rest_framework.test import APITestCase

from orthos2.data.models import Machine, ReservationHistory


class ReservationHistoryTest(APITestCase):
    """
    Test that the RESERVATIONHISTORY command no longer exposes a username.
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

        self.machine = Machine.objects.get(fqdn="testsys.orthos2.test")
        now = datetime.datetime.now()
        ReservationHistory.objects.create(
            machine=self.machine,
            reserved_at=now - datetime.timedelta(days=7),
            reserved_until=now,
            reserved_reason="Done testing",
        )

    def test_history_response_has_no_user_field(self) -> None:
        url = reverse("api:history")
        url += "?fqdn=testsys.orthos2.test"

        response = self.client.get(url, format="json")
        json_response = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        theader_keys = {
            key for column in json_response["header"]["theader"] for key in column
        }
        self.assertNotIn("user", theader_keys)

        self.assertEqual(len(json_response["data"]), 1)
        entry = json_response["data"][0]
        self.assertNotIn("user", entry)
        self.assertIn("at", entry)
        self.assertIn("until", entry)
        self.assertEqual(entry["reason"], "Done testing")
