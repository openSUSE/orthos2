from django.urls import reverse  # type: ignore
from django_webtest import WebTest  # type: ignore

from orthos2.data.models import Domain
from orthos2.data.models.serverconfig import ServerConfig
from orthos2.frontend.views.statistics import _domain_color


class Statistics(WebTest):

    csrf_checks = True

    fixtures = []  # type: ignore

    def test_statistics_view(self) -> None:
        """Test if statistics view comes up."""
        page = self.app.get(reverse("frontend:free_machines"), user="user")  # type: ignore

        self.assertEqual(page.context["user"].username, "user")  # type: ignore

        page = page.click("Statistics").maybe_follow()  # type: ignore

        self.assertContains(page, "Numbers")  # type: ignore

    def test_domains_have_deterministic_colors_across_requests(self) -> None:
        """The color assigned to a domain must not change between requests."""
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        Domain.objects.create(
            name="statistics-color-test.orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )

        first = self.app.get(reverse("frontend:statistics"), user="user").context["data"]  # type: ignore
        second = self.app.get(reverse("frontend:statistics"), user="user").context["data"]  # type: ignore

        self.assertEqual(first["domains"]["colors"], second["domains"]["colors"])


class DomainColorTests(WebTest):

    fixtures = []  # type: ignore

    def test_same_domain_name_always_gets_same_color(self) -> None:
        self.assertEqual(
            _domain_color("example.orthos2.test"), _domain_color("example.orthos2.test")
        )

    def test_different_domain_names_get_different_colors(self) -> None:
        self.assertNotEqual(
            _domain_color("a.orthos2.test"), _domain_color("b.orthos2.test")
        )

    def test_color_is_a_hex_triplet(self) -> None:
        self.assertRegex(_domain_color("example.orthos2.test"), r"^#[0-9A-Fa-f]{6}$")
