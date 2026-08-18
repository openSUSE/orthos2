"""Tests for the DomainAdmin (domain architecture) CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Architecture, Domain, DomainAdmin, ServerConfig


class DomainArchitectureViewTestCase(TestCase):
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
        self.architecture = Architecture.objects.get(name="x86_64")
        self.domainarchitecture = DomainAdmin.objects.create(
            domain=self.domain,
            arch=self.architecture,
            contact_email="support@orthos2.test",
        )


class DomainArchitectureListViewTest(DomainArchitectureViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:domain_architectures", kwargs={"domain_id": self.domain.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:domain_architectures", kwargs={"domain_id": self.domain.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_domainarchitectures(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:domain_architectures", kwargs={"domain_id": self.domain.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"x86_64" in response.content
        assert b"support@orthos2.test" in response.content


class NewDomainArchitectureViewTest(DomainArchitectureViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:new_domain_architecture", kwargs={"domain_id": self.domain.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:new_domain_architecture", kwargs={"domain_id": self.domain.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:new_domain_architecture", kwargs={"domain_id": self.domain.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_domainarchitecture(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        other_arch = Architecture.objects.get(name="ppc")
        url = reverse(
            "frontend:new_domain_architecture", kwargs={"domain_id": self.domain.pk}
        )
        response = self.client.post(
            url,
            {"arch": other_arch.pk, "contact_email": "ppc@orthos2.test"},
        )
        assert response.status_code == 302
        assert DomainAdmin.objects.filter(domain=self.domain, arch=other_arch).exists()

    def test_regular_user_post_does_not_create_domainarchitecture(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        other_arch = Architecture.objects.get(name="ppc")
        url = reverse(
            "frontend:new_domain_architecture", kwargs={"domain_id": self.domain.pk}
        )
        response = self.client.post(
            url,
            {"arch": other_arch.pk, "contact_email": "ppc@orthos2.test"},
        )
        assert response.status_code == 403
        assert not DomainAdmin.objects.filter(
            domain=self.domain, arch=other_arch
        ).exists()


class DomainArchitectureDetailedEditViewTest(DomainArchitectureViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:edit_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_domainarchitecture(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.post(
            url,
            {"arch": self.architecture.pk, "contact_email": "new@orthos2.test"},
        )
        assert response.status_code == 302
        self.domainarchitecture.refresh_from_db()
        assert self.domainarchitecture.contact_email == "new@orthos2.test"

    def test_regular_user_post_does_not_update_domainarchitecture(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.post(
            url,
            {"arch": self.architecture.pk, "contact_email": "new@orthos2.test"},
        )
        assert response.status_code == 403
        self.domainarchitecture.refresh_from_db()
        assert self.domainarchitecture.contact_email == "support@orthos2.test"


class DeleteDomainArchitectureViewTest(DomainArchitectureViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:delete_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_domainarchitecture(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert not DomainAdmin.objects.filter(pk=self.domainarchitecture.pk).exists()

    def test_regular_user_post_does_not_delete_domainarchitecture(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_domain_architecture",
            kwargs={"pk": self.domainarchitecture.pk},
        )
        response = self.client.post(url)
        assert response.status_code == 403
        assert DomainAdmin.objects.filter(pk=self.domainarchitecture.pk).exists()
