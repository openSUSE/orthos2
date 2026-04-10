from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Domain, Machine


class RegenerateCobblerPruneViewTests(TestCase):
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def setUp(self) -> None:
        settings.SECRET_KEY = "test-secret-key"
        user_model = get_user_model()
        self.user = user_model.objects.get(username="superuser")
        self.client.force_login(self.user)

        self.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        Domain.objects.filter(name="orthos2.test").update(
            cobbler_server=self.cobbler_server
        )

    @mock.patch("orthos2.frontend.views.machine.CobblerServer")
    def test_cleanup_domain_cobbler_diff(
        self, mocked_cobbler_server: mock.MagicMock
    ) -> None:
        mocked_cobbler_server.return_value.get_machines.return_value = [
            "testsys.orthos2.test",
            "stale.orthos2.test",
            "other.foreign.test",
        ]

        response = self.client.get(
            reverse(
                "frontend:cleanup_domain_cobbler_page", args=[self.cobbler_server.id]
            ),
        )

        self.assertEqual(response.status_code, 200)
        # Contained in the JSON test fixture
        self.assertNotContains(response, "testsys.orthos2.test")
        self.assertContains(response, "stale.orthos2.test")
        self.assertContains(response, "other.foreign.test")

    @mock.patch("orthos2.frontend.views.machine.CobblerServer")
    def test_cleanup_domain_cobbler_prune(
        self, mocked_cobbler_server: mock.MagicMock
    ) -> None:
        mocked_server = mocked_cobbler_server.return_value
        mocked_server.get_machines.return_value = [
            "testsys.orthos2.test",
            "stale.orthos2.test",
            "other.foreign.test",
        ]

        response = self.client.post(
            reverse(
                "frontend:cleanup_domain_cobbler_page", args=[self.cobbler_server.id]
            ),
            {
                "fqdn": ["stale.orthos2.test", "other.foreign.test"],
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "frontend:cleanup_domain_cobbler_page", args=[self.cobbler_server.id]
            ),
        )
        mocked_server.remove_by_name.assert_any_call("stale.orthos2.test")
        mocked_server.remove_by_name.assert_any_call("other.foreign.test")

    @mock.patch("orthos2.frontend.views.regenerate.signal_cobbler_regenerate.send")
    def test_regenerate_domain_cobbler_triggers_regeneration(
        self, mocked_signal_send: mock.MagicMock
    ) -> None:
        response = self.client.get(
            reverse("frontend:regenerate_domain_cobbler", args=[self.cobbler_server.id])
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["message"], "Regeneration started")
        mocked_signal_send.assert_called_once_with(sender=None, domain_id=1)

    def test_cleanup_domain_cobbler_page(self) -> None:
        response = self.client.get(
            reverse(
                "frontend:cleanup_domain_cobbler_page", args=[self.cobbler_server.id]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cobbler Cleanup")
        self.assertContains(response, self.cobbler_server.fqdn)
