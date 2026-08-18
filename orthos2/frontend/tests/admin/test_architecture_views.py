"""Tests for the Architecture CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Architecture


class ArchitectureListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        Architecture.objects.create(name="AcmeArchitecture")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:architectures")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:architectures")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_architectures(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:architectures")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeArchitecture" in response.content


class ArchitectureDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.architecture = Architecture.objects.create(name="AcmeArchitecture")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:architecture_detail", kwargs={"id": self.architecture.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:architecture_detail", kwargs={"id": self.architecture.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:architecture_detail", kwargs={"id": self.architecture.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeArchitecture" in response.content

    def test_nonexistent_architecture_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:architecture_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewArchitectureViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_architecture")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_architecture")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_architecture")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_architecture(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_architecture")
        response = self.client.post(url, {"name": "AcmeArchitecture"})
        assert response.status_code == 302
        assert Architecture.objects.filter(name="AcmeArchitecture").exists()

    def test_regular_user_post_does_not_create_architecture(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_architecture")
        response = self.client.post(url, {"name": "AcmeArchitecture"})
        assert response.status_code == 403
        assert not Architecture.objects.filter(name="AcmeArchitecture").exists()


class ArchitectureDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.architecture = Architecture.objects.create(name="AcmeArchitecture")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_architecture", kwargs={"pk": self.architecture.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_architecture", kwargs={"pk": self.architecture.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_architecture", kwargs={"pk": self.architecture.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_architecture(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_architecture", kwargs={"pk": self.architecture.pk})
        response = self.client.post(url, {"name": "AcmeArchitecture Renamed"})
        assert response.status_code == 302
        self.architecture.refresh_from_db()
        assert self.architecture.name == "AcmeArchitecture Renamed"

    def test_regular_user_post_does_not_update_architecture(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_architecture", kwargs={"pk": self.architecture.pk})
        response = self.client.post(url, {"name": "AcmeArchitecture Renamed"})
        assert response.status_code == 403
        self.architecture.refresh_from_db()
        assert self.architecture.name == "AcmeArchitecture"


class DeleteArchitectureViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.architecture = Architecture.objects.create(name="AcmeArchitecture")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:delete_architecture", kwargs={"pk": self.architecture.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_architecture", kwargs={"pk": self.architecture.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_architecture", kwargs={"pk": self.architecture.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_architecture(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_architecture", kwargs={"pk": self.architecture.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Architecture.objects.filter(pk=self.architecture.pk).exists()

    def test_regular_user_post_does_not_delete_architecture(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_architecture", kwargs={"pk": self.architecture.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 403
        assert Architecture.objects.filter(pk=self.architecture.pk).exists()


class DeleteArchitectureProtectionViewTest(TestCase):
    """Architectures referenced by machines must not be deletable."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_superuser_post_cannot_delete_architecture_with_machines(self) -> None:
        # Architecture pk=1 (x86_64) is referenced by fixture machines.
        architecture = Architecture.objects.get(pk=1)
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_architecture", kwargs={"pk": architecture.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert Architecture.objects.filter(pk=architecture.pk).exists()
