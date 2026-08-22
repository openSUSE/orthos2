"""Tests for the "NetBox Synchronized" filter on the Machine list."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Architecture, Domain, Machine, ServerConfig, System


class MachineListHasNetboxFilterTest(TestCase):
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
        self.synced_machine = Machine.objects.create(
            fqdn="synced-machine.orthos2.test",
            system=system,
            architecture=architecture,
            netbox_id=42,
        )
        self.unsynced_machine = Machine.objects.create(
            fqdn="plain-machine.orthos2.test", system=system, architecture=architecture
        )

    def test_no_filter_shows_both(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(reverse("frontend:machines"))
        assert b"synced-machine.orthos2.test" in response.content
        assert b"plain-machine.orthos2.test" in response.content

    def test_filter_has_netbox_yes(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(reverse("frontend:machines"), {"has_netbox": "1"})
        assert b"synced-machine.orthos2.test" in response.content
        assert b"plain-machine.orthos2.test" not in response.content

    def test_filter_has_netbox_no(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(reverse("frontend:machines"), {"has_netbox": "0"})
        assert b"plain-machine.orthos2.test" in response.content
        assert b"synced-machine.orthos2.test" not in response.content
