"""Tests for the System CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import System


class SystemListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        System.objects.create(name="AcmeSystem")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:systems")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:systems")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_systems(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:systems")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeSystem" in response.content


class SystemDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.system = System.objects.create(name="AcmeSystem")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:system_detail", kwargs={"id": self.system.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:system_detail", kwargs={"id": self.system.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:system_detail", kwargs={"id": self.system.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeSystem" in response.content

    def test_nonexistent_system_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:system_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewSystemViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_system")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_system")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_system")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_system(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_system")
        response = self.client.post(url, {"name": "AcmeSystem"})
        assert response.status_code == 302
        assert System.objects.filter(name="AcmeSystem").exists()

    def test_regular_user_post_does_not_create_system(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_system")
        response = self.client.post(url, {"name": "AcmeSystem"})
        assert response.status_code == 403
        assert not System.objects.filter(name="AcmeSystem").exists()


class SystemDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.system = System.objects.create(name="AcmeSystem")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_system", kwargs={"pk": self.system.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_system", kwargs={"pk": self.system.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_system", kwargs={"pk": self.system.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_system(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_system", kwargs={"pk": self.system.pk})
        response = self.client.post(url, {"name": "AcmeSystem Renamed"})
        assert response.status_code == 302
        self.system.refresh_from_db()
        assert self.system.name == "AcmeSystem Renamed"

    def test_regular_user_post_does_not_update_system(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_system", kwargs={"pk": self.system.pk})
        response = self.client.post(url, {"name": "AcmeSystem Renamed"})
        assert response.status_code == 403
        self.system.refresh_from_db()
        assert self.system.name == "AcmeSystem"


class DeleteSystemViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.system = System.objects.create(name="AcmeSystem")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_system", kwargs={"pk": self.system.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_system", kwargs={"pk": self.system.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_system", kwargs={"pk": self.system.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_system(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_system", kwargs={"pk": self.system.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not System.objects.filter(pk=self.system.pk).exists()

    def test_regular_user_post_does_not_delete_system(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_system", kwargs={"pk": self.system.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert System.objects.filter(pk=self.system.pk).exists()
