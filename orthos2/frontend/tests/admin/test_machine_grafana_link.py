"""Tests for the Grafana dashboard links on the machine detail page."""

from django.test import override_settings
from django.urls import reverse  # type: ignore
from django_webtest import WebTest  # type: ignore

from orthos2.data.models import BMC, Architecture, Machine, RemotePowerType, System
from orthos2.data.models.domain import Domain
from orthos2.data.models.serverconfig import ServerConfig


class MachineDetailGrafanaLinkTest(WebTest):
    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
        "orthos2/data/fixtures/architectures.json",
    ]

    def setUp(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        Domain(
            name="foo.orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        ).save()

        architecture_id = (
            Architecture.get_architecture_manager().get_by_natural_key("x86_64").id
        )
        system = System.get_system_manager().get_by_natural_key("BareMetal")

        self.machine_without_bmc = Machine()
        self.machine_without_bmc.pk = 1
        self.machine_without_bmc.system = system
        self.machine_without_bmc.fqdn = "machine1.foo.orthos2.test"
        self.machine_without_bmc.architecture_id = architecture_id
        self.machine_without_bmc.save()

        self.machine_with_bmc = Machine()
        self.machine_with_bmc.pk = 2
        self.machine_with_bmc.system = system
        self.machine_with_bmc.fqdn = "machine2.foo.orthos2.test"
        self.machine_with_bmc.architecture_id = architecture_id
        self.machine_with_bmc.save()

        ipmi_fence_agent = RemotePowerType.objects.create(
            name="ipmilanplus", device="bmc"
        )
        BMC.objects.create(
            username="root",
            password="root",
            fqdn="machine2-sp.foo.orthos2.test",
            mac="AA:BB:CC:DD:EE:FF",
            machine=self.machine_with_bmc,
            fence_agent=ipmi_fence_agent,
        )

    @override_settings(
        GRAFANA_URL="https://grafana.arch-mgmt.prg2.suse.org",
        GRAFANA_HOST_DASHBOARD_UID="fd234888-992a-4855-a11d-22669e3c3b60",
    )
    def test_shows_host_and_bmc_links_when_machine_has_bmc(self) -> None:
        page = self.app.get(  # type: ignore
            reverse("frontend:detail", args=["2"]), user="superuser"
        )

        self.assertContains(page, "Grafana Dashboard")  # type: ignore
        self.assertContains(page, "Grafana Dashboard (BMC)")  # type: ignore
        self.assertContains(  # type: ignore
            page,
            "https://grafana.arch-mgmt.prg2.suse.org/d/fd234888-992a-4855-a11d-22669e3c3b60/"
            "orthos-2-host-details?var-instance=machine2.foo.orthos2.test",
        )
        self.assertContains(  # type: ignore
            page,
            "https://grafana.arch-mgmt.prg2.suse.org/d/fd234888-992a-4855-a11d-22669e3c3b60/"
            "orthos-2-host-details?var-instance=machine2-sp.foo.orthos2.test",
        )

    @override_settings(
        GRAFANA_URL="https://grafana.arch-mgmt.prg2.suse.org",
        GRAFANA_HOST_DASHBOARD_UID="fd234888-992a-4855-a11d-22669e3c3b60",
    )
    def test_shows_only_host_link_when_machine_has_no_bmc(self) -> None:
        page = self.app.get(  # type: ignore
            reverse("frontend:detail", args=["1"]), user="superuser"
        )

        self.assertContains(page, "Grafana Dashboard")  # type: ignore
        self.assertNotContains(page, "Grafana Dashboard (BMC)")  # type: ignore

    @override_settings(GRAFANA_URL="")
    def test_hides_grafana_links_when_not_configured(self) -> None:
        page = self.app.get(  # type: ignore
            reverse("frontend:detail", args=["2"]), user="superuser"
        )

        self.assertNotContains(page, "Grafana Dashboard")  # type: ignore
