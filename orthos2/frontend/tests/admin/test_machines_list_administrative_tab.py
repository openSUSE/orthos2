"""Tests for the "Administrative Machines" tab on the Machine list."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Architecture, Domain, Machine, ServerConfig, System


class AdministrativeMachineListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        system = System.objects.get(name="BareMetal")
        architecture = Architecture.objects.get(name="x86_64")
        self.administrative_machine = Machine.objects.create(
            fqdn="administrative-machine.orthos2.test",
            system=system,
            architecture=architecture,
            administrative=True,
        )
        self.plain_machine = Machine.objects.create(
            fqdn="plain-machine.orthos2.test",
            system=system,
            architecture=architecture,
        )

    def test_superuser_sees_only_administrative_machines(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        response = self.client.get(reverse("frontend:administrative_machines"))
        assert b"administrative-machine.orthos2.test" in response.content
        assert b"plain-machine.orthos2.test" not in response.content

    def test_regular_user_sees_no_administrative_machines(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(reverse("frontend:administrative_machines"))
        assert b"administrative-machine.orthos2.test" not in response.content
        assert b"plain-machine.orthos2.test" not in response.content

    def test_superuser_sees_administrative_machines_nav_link(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        response = self.client.get(reverse("frontend:machines"))
        assert b"Administrative Machines" in response.content

    def test_regular_user_does_not_see_administrative_machines_nav_link(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(reverse("frontend:machines"))
        assert b"Administrative Machines" not in response.content
