"""Tests for the Enclosure CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Enclosure


class EnclosureListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        Enclosure.objects.create(name="AcmeEnclosure")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:enclosures")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:enclosures")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_enclosures(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:enclosures")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeEnclosure" in response.content


class EnclosureDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.enclosure = Enclosure.objects.create(name="AcmeEnclosure")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:enclosure_detail", kwargs={"id": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_redirects_to_login(self) -> None:
        # enclosure_detail is gated by the bare @permission_required
        # decorator, which redirects rather than raises PermissionDenied
        # for authenticated users lacking the permission.
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:enclosure_detail", kwargs={"id": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:enclosure_detail", kwargs={"id": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeEnclosure" in response.content

    def test_nonexistent_enclosure_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:enclosure_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class EnclosureMachinesViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.enclosure = Enclosure.objects.create(name="AcmeEnclosure")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:enclosure_machines", kwargs={"id": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_redirects_to_login(self) -> None:
        # enclosure_machines is gated by the bare @permission_required
        # decorator, which redirects rather than raises PermissionDenied
        # for authenticated users lacking the permission.
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:enclosure_machines", kwargs={"id": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_superuser_get_shows_machines_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:enclosure_machines", kwargs={"id": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 200


class NewEnclosureViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_enclosure")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_enclosure")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_enclosure")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_enclosure(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_enclosure")
        response = self.client.post(url, {"name": "AcmeEnclosure", "netbox_id": 0})
        assert response.status_code == 302
        assert Enclosure.objects.filter(name="AcmeEnclosure").exists()

    def test_regular_user_post_does_not_create_enclosure(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_enclosure")
        response = self.client.post(url, {"name": "AcmeEnclosure", "netbox_id": 0})
        assert response.status_code == 403
        assert not Enclosure.objects.filter(name="AcmeEnclosure").exists()


class EnclosureDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.enclosure = Enclosure.objects.create(name="AcmeEnclosure")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_enclosure(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.post(
            url, {"name": "AcmeEnclosure Renamed", "netbox_id": 0}
        )
        assert response.status_code == 302
        self.enclosure.refresh_from_db()
        assert self.enclosure.name == "AcmeEnclosure Renamed"

    def test_regular_user_post_does_not_update_enclosure(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.post(
            url, {"name": "AcmeEnclosure Renamed", "netbox_id": 0}
        )
        assert response.status_code == 403
        self.enclosure.refresh_from_db()
        assert self.enclosure.name == "AcmeEnclosure"


class EnclosureNetboxComparisonViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.enclosure = Enclosure.objects.create(name="AcmeEnclosure")

    def test_regular_user_get_is_redirected_with_error(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:enclosure_netbox_comparisons", kwargs={"id": self.enclosure.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302

    def test_superuser_get_shows_comparison_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:enclosure_netbox_comparisons", kwargs={"id": self.enclosure.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200


class DeleteEnclosureViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.enclosure = Enclosure.objects.create(name="AcmeEnclosure")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_enclosure(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Enclosure.objects.filter(pk=self.enclosure.pk).exists()

    def test_regular_user_post_does_not_delete_enclosure(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_enclosure", kwargs={"pk": self.enclosure.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert Enclosure.objects.filter(pk=self.enclosure.pk).exists()
