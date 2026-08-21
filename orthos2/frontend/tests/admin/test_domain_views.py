"""Tests for the Domain CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Architecture, Domain, Machine, ServerConfig, System


class DomainListViewTest(TestCase):
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

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:domains")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:domains")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_domains(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:domains")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"orthos2.test" in response.content


class DomainDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        self.domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:domain_detail", kwargs={"id": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:domain_detail", kwargs={"id": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:domain_detail", kwargs={"id": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"orthos2.test" in response.content

    def test_nonexistent_domain_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:domain_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404

    def test_superuser_get_hides_regenerate_buttons_without_servers(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:domain_detail", kwargs={"id": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Regenerate Cobbler Server" not in response.content
        assert b"Regenerate Serial Console Server" not in response.content

    def test_superuser_get_shows_cobbler_and_cscreen_server_links(self) -> None:
        cobbler_server = Machine.objects.create(
            fqdn="cobbler.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        cscreen_server = Machine.objects.create(
            fqdn="cscreen.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        self.domain.cobbler_server = cobbler_server
        self.domain.cscreen_server = cscreen_server
        self.domain.save()

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:domain_detail", kwargs={"id": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Regenerate Cobbler Server" in response.content
        assert b"Regenerate Serial Console Server" in response.content
        assert (
            reverse("frontend:detail", kwargs={"id": cobbler_server.pk}).encode()
            in response.content
        )
        assert (
            reverse("frontend:detail", kwargs={"id": cscreen_server.pk}).encode()
            in response.content
        )


class NewDomainViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")

    def _payload(self) -> dict:
        return {
            "name": "orthos2.test",
            "cobbler_server_username": "cobbler",
            "cobbler_server_password": "cobbler",
            "ip_v4": "127.0.0.1",
            "ip_v6": "::1",
            "subnet_mask_v4": 24,
            "subnet_mask_v6": 64,
            "enable_v4": "on",
            "enable_v6": "on",
            "dynamic_range_v4_start": "127.0.0.1",
            "dynamic_range_v4_end": "127.0.0.1",
            "dynamic_range_v6_start": "::1",
            "dynamic_range_v6_end": "::1",
        }

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_domain")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_domain")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_domain")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_domain(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_domain")
        response = self.client.post(url, self._payload())
        assert response.status_code == 302
        assert Domain.objects.filter(name="orthos2.test").exists()

    def test_regular_user_post_does_not_create_domain(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_domain")
        response = self.client.post(url, self._payload())
        assert response.status_code == 403
        assert not Domain.objects.filter(name="orthos2.test").exists()


class DomainDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        self.domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )

    def _payload(self, **overrides) -> dict:
        payload = {
            "name": "orthos2.test",
            "cobbler_server_username": "cobbler",
            "cobbler_server_password": "cobbler",
            "ip_v4": "127.0.0.1",
            "ip_v6": "::1",
            "subnet_mask_v4": 24,
            "subnet_mask_v6": 64,
            "enable_v4": "on",
            "enable_v6": "on",
            "dynamic_range_v4_start": "127.0.0.1",
            "dynamic_range_v4_end": "127.0.0.1",
            "dynamic_range_v6_start": "::1",
            "dynamic_range_v6_end": "::1",
        }
        payload.update(overrides)
        return payload

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_domain", kwargs={"pk": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_domain", kwargs={"pk": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_domain", kwargs={"pk": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_domain(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_domain", kwargs={"pk": self.domain.pk})
        response = self.client.post(
            url, self._payload(cobbler_server_username="newuser")
        )
        assert response.status_code == 302
        self.domain.refresh_from_db()
        assert self.domain.cobbler_server_username == "newuser"

    def test_regular_user_post_does_not_update_domain(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_domain", kwargs={"pk": self.domain.pk})
        response = self.client.post(
            url, self._payload(cobbler_server_username="newuser")
        )
        assert response.status_code == 403
        self.domain.refresh_from_db()
        assert self.domain.cobbler_server_username != "newuser"


class DeleteDomainViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        self.domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_domain", kwargs={"pk": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_domain", kwargs={"pk": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_domain", kwargs={"pk": self.domain.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_domain(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_domain", kwargs={"pk": self.domain.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Domain.objects.filter(pk=self.domain.pk).exists()

    def test_regular_user_post_does_not_delete_domain(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_domain", kwargs={"pk": self.domain.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert Domain.objects.filter(pk=self.domain.pk).exists()


class DeleteDomainProtectionViewTest(TestCase):
    """Domains referenced by machines must not be deletable."""

    fixtures = [
        "orthos2/data/fixtures/tests/test_machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_superuser_post_cannot_delete_domain_with_machines(self) -> None:
        domain = Domain.objects.get(pk=1)
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_domain", kwargs={"pk": domain.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert Domain.objects.filter(pk=domain.pk).exists()
