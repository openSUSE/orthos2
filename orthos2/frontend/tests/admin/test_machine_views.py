from unittest import mock

from django.urls import reverse
from django_webtest import WebTest  # type: ignore

from orthos2.data.models import Architecture, Machine, ServerConfig, System
from orthos2.data.models.domain import Domain


class ChangeView(WebTest):

    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
        "orthos2/data/fixtures/architectures.json",
    ]

    @mock.patch("orthos2.data.models.machine.is_dns_resolvable")
    def setUp(self, m_is_dns_resolvable):
        m_is_dns_resolvable.return_value = True

        ServerConfig.objects.create(key="domain.validendings", value="bar.de")

        Domain(
            name="foo.bar.de",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        ).save()

        m1 = Machine()
        m1.pk = 1
        m1.system = System.objects.get_by_natural_key("BareMetal")
        m1.fqdn = "machine1.foo.bar.de"
        m1.architecture_id = Architecture.objects.get_by_natural_key("x86_64").id

        m1.save()

        m2 = Machine()
        m2.pk = 2
        m2.administrative = True
        m2.system = System.objects.get_by_natural_key("BareMetal")
        m2.fqdn = "machine2.foo.bar.de"
        m2.architecture_id = Architecture.objects.get_by_natural_key("x86_64").id

        m2.save()

    def test_visible_fieldsets_non_administrative_systems(self) -> None:
        """Test for fieldsets."""
        # Act
        page = self.app.get(
            reverse("admin:data_machine_change", args=["1"]), user="superuser"
        )

        # Assert
        self.assertContains(page, "VIRTUALIZATION")

    def test_visible_inlines_non_administrative_systems(self) -> None:
        """Test for inlines."""
        # Act
        page = self.app.get(
            reverse("admin:data_machine_change", args=["1"]), user="superuser"
        )

        # Assert
        self.assertContains(page, "Add another Serial Console")
        self.assertContains(page, "Remote Power")

    def test_visible_fieldsets_administrative_systems(self) -> None:
        """Test for fieldsets."""
        # Act
        page = self.app.get(
            reverse("admin:data_machine_change", args=["2"]), user="superuser"
        )

        # Assert
        self.assertContains(page, "VIRTUALIZATION")

    def test_visible_inlines_administrative_systems(self) -> None:
        """Test for inlines."""
        # Act
        page = self.app.get(
            reverse("admin:data_machine_change", args=["2"]), user="superuser"
        )

        # Assert
        self.assertContains(page, "Add another Serial Console")
        self.assertContains(page, "Remote Power")
