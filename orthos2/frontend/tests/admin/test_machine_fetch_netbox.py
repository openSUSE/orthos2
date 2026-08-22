"""Tests for the Machine "Fetch Netbox" action guard."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Architecture, Domain, Machine, ServerConfig, System
from orthos2.taskmanager.models import SingleTask


class MachineFetchNetboxViewTest(TestCase):
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
        self.system = System.objects.get(name="BareMetal")
        self.architecture = Architecture.objects.get(name="x86_64")
        self.machine = Machine.objects.create(
            fqdn="synced.orthos2.test",
            system=self.system,
            architecture=self.architecture,
            netbox_id=42,
        )

    def test_superuser_queues_fetch_task(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:netbox_fetch", kwargs={"id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert SingleTask.objects.filter(name="NetboxFetchFullMachine").exists()

    def test_superuser_get_when_not_synced_does_not_queue_task(self) -> None:
        unsynced = Machine.objects.create(
            fqdn="unsynced.orthos2.test",
            system=self.system,
            architecture=self.architecture,
        )
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:netbox_fetch", kwargs={"id": unsynced.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert not SingleTask.objects.filter(name="NetboxFetchFullMachine").exists()


class MachineCompareNetboxViewTest(TestCase):
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
        self.system = System.objects.get(name="BareMetal")
        self.architecture = Architecture.objects.get(name="x86_64")
        self.machine = Machine.objects.create(
            fqdn="synced.orthos2.test",
            system=self.system,
            architecture=self.architecture,
            netbox_id=42,
        )

    def test_superuser_queues_compare_task(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:netbox_compare", kwargs={"id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert SingleTask.objects.filter(name="NetboxCompareFullMachine").exists()

    def test_superuser_get_when_not_synced_does_not_queue_task(self) -> None:
        unsynced = Machine.objects.create(
            fqdn="unsynced.orthos2.test",
            system=self.system,
            architecture=self.architecture,
        )
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:netbox_compare", kwargs={"id": unsynced.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert not SingleTask.objects.filter(name="NetboxCompareFullMachine").exists()
