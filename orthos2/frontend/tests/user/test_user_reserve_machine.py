"""
Tests for reserving a machine on behalf of another user.
"""

import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import BMC, Machine, ServerConfig


class UserReserveMachineViewTest(TestCase):
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def setUp(self) -> None:
        # Machine.save() calls validate_domain_ending() which requires this ServerConfig.
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")

        self.machine = Machine.objects.get(fqdn="testsys.orthos2.test")
        # The fixture attaches a BMC to this BareMetal machine, but Machine.save()
        # raises ValidationError when BareMetal + BMC (allowBMC is unset in fixtures).
        # Remove the BMC so reserve() → save() succeeds.
        BMC.objects.filter(machine=self.machine).delete()
        self.superuser = User.objects.get(username="superuser")
        self.regular_user = User.objects.get(username="user")
        self.target_user = User.objects.create_user(
            username="targetuser", password="linux", email="target@example.com"
        )

    def _reserve_url(self, user_id: int) -> str:
        return reverse("frontend:user_reserve_machine", args=[user_id])

    def _detail_url(self, user_id: int) -> str:
        return reverse("frontend:user_detail", args=[user_id])

    def test_sidebar_contains_reserve_link(self) -> None:
        self.client.force_login(self.superuser)
        response = self.client.get(self._detail_url(self.target_user.pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("frontend:user_reserve_machine", args=[self.target_user.pk]),
        )

    def test_reserve_form_accessible_for_superuser(self) -> None:
        self.client.force_login(self.superuser)
        response = self.client.get(self._reserve_url(self.target_user.pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Machine FQDN")
        self.assertContains(response, "Reason")
        self.assertContains(response, "Until")

    def test_reserve_form_forbidden_for_non_superuser(self) -> None:
        self.client.force_login(self.regular_user)
        response = self.client.get(self._reserve_url(self.target_user.pk))
        self.assertEqual(response.status_code, 403)

    def test_reserve_success(self) -> None:
        self.client.force_login(self.superuser)
        future_date = (datetime.date.today() + datetime.timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )

        response = self.client.post(
            self._reserve_url(self.target_user.pk),
            {
                "machine": self.machine.fqdn,
                "reason": "Physical owner needs this machine",
                "until": future_date,
            },
        )

        self.assertRedirects(response, self._detail_url(self.target_user.pk))
        self.machine.refresh_from_db()
        self.assertEqual(self.machine.reserved_by, self.target_user)
        self.assertNotEqual(self.machine.reserved_by, self.superuser)

    def test_reserve_invalid_fqdn(self) -> None:
        self.client.force_login(self.superuser)
        future_date = (datetime.date.today() + datetime.timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )

        response = self.client.post(
            self._reserve_url(self.target_user.pk),
            {
                "machine": "nonexistent.orthos2.test",
                "reason": "Test reason",
                "until": future_date,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not found")
        self.machine.refresh_from_db()
        self.assertIsNone(self.machine.reserved_by)

    def test_reserve_date_too_far(self) -> None:
        self.client.force_login(self.superuser)
        far_date = (datetime.date.today() + datetime.timedelta(days=120)).strftime(
            "%Y-%m-%d"
        )

        response = self.client.post(
            self._reserve_url(self.target_user.pk),
            {
                "machine": self.machine.fqdn,
                "reason": "Test reason",
                "until": far_date,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reservation period is limited")
        self.machine.refresh_from_db()
        self.assertIsNone(self.machine.reserved_by)

    def test_reserve_infinite_date(self) -> None:
        self.client.force_login(self.superuser)

        response = self.client.post(
            self._reserve_url(self.target_user.pk),
            {
                "machine": self.machine.fqdn,
                "reason": "Permanent owner reservation",
                "until": "9999-12-31",
            },
        )

        self.assertRedirects(response, self._detail_url(self.target_user.pk))
        self.machine.refresh_from_db()
        self.assertEqual(self.machine.reserved_by, self.target_user)
        self.assertEqual(self.machine.reserved_until.date(), datetime.date.max)
