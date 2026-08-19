"""Tests for the Manufacturer CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Manufacturer


class ManufacturerListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:manufacturers")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:manufacturers")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_manufacturers(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:manufacturers")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeCorp" in response.content


class ManufacturerDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:manufacturer_detail", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:manufacturer_detail", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:manufacturer_detail", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeCorp" in response.content

    def test_nonexistent_manufacturer_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:manufacturer_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewManufacturerViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_manufacturer")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_manufacturer")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_manufacturer")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_manufacturer(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_manufacturer")
        response = self.client.post(url, {"name": "AcmeSubsidiary"})
        assert response.status_code == 302
        assert Manufacturer.objects.filter(name="AcmeSubsidiary").exists()

    def test_regular_user_post_does_not_create_manufacturer(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_manufacturer")
        response = self.client.post(url, {"name": "AcmeSubsidiary"})
        assert response.status_code == 403
        assert not Manufacturer.objects.filter(name="AcmeSubsidiary").exists()


class ManufacturerDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_manufacturer", kwargs={"pk": self.manufacturer.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_manufacturer", kwargs={"pk": self.manufacturer.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_manufacturer", kwargs={"pk": self.manufacturer.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_manufacturer(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_manufacturer", kwargs={"pk": self.manufacturer.pk})
        response = self.client.post(url, {"name": "AcmeCorp Renamed"})
        assert response.status_code == 302
        self.manufacturer.refresh_from_db()
        assert self.manufacturer.name == "AcmeCorp Renamed"

    def test_regular_user_post_does_not_update_manufacturer(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_manufacturer", kwargs={"pk": self.manufacturer.pk})
        response = self.client.post(url, {"name": "AcmeCorp Renamed"})
        assert response.status_code == 403
        self.manufacturer.refresh_from_db()
        assert self.manufacturer.name == "AcmeCorp"


class DeleteManufacturerViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:delete_manufacturer", kwargs={"pk": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_manufacturer", kwargs={"pk": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_manufacturer", kwargs={"pk": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_manufacturer(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_manufacturer", kwargs={"pk": self.manufacturer.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Manufacturer.objects.filter(pk=self.manufacturer.pk).exists()

    def test_regular_user_post_does_not_delete_manufacturer(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_manufacturer", kwargs={"pk": self.manufacturer.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 403
        assert Manufacturer.objects.filter(pk=self.manufacturer.pk).exists()
