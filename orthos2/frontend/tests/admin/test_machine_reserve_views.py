"""Tests for the machine_reserve frontend view."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import BMC, Machine, ServerConfig


class MachineReserveViewTest(TestCase):
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def setUp(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        self.machine = Machine.objects.get(pk=1)
        if hasattr(self.machine, "bmc"):
            BMC.objects.filter(machine=self.machine).delete()

    def test_superuser_get_shows_cancel_link_to_machine_detail(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:reserve_machine", kwargs={"id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        self.assertContains(response, "Cancel")
        self.assertContains(
            response, reverse("frontend:detail", kwargs={"id": self.machine.pk})
        )
