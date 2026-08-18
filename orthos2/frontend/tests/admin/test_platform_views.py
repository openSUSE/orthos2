"""Tests for the Platform CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Manufacturer, Platform


class PlatformListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        Platform.objects.create(name="AcmePlatform", manufacturer=manufacturer)

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:platforms")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:platforms")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_platforms(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:platforms")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmePlatform" in response.content


class PlatformDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.platform = Platform.objects.create(
            name="AcmePlatform", manufacturer=manufacturer
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:platform_detail", kwargs={"id": self.platform.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:platform_detail", kwargs={"id": self.platform.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:platform_detail", kwargs={"id": self.platform.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmePlatform" in response.content

    def test_nonexistent_platform_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:platform_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewPlatformViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_platform")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_platform")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_platform")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_platform(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_platform")
        response = self.client.post(
            url, {"name": "AcmePlatform", "manufacturer": self.manufacturer.pk}
        )
        assert response.status_code == 302
        assert Platform.objects.filter(name="AcmePlatform").exists()

    def test_regular_user_post_does_not_create_platform(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_platform")
        response = self.client.post(
            url, {"name": "AcmePlatform", "manufacturer": self.manufacturer.pk}
        )
        assert response.status_code == 403
        assert not Platform.objects.filter(name="AcmePlatform").exists()


class PlatformDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.platform = Platform.objects.create(
            name="AcmePlatform", manufacturer=self.manufacturer
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_platform", kwargs={"pk": self.platform.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_platform", kwargs={"pk": self.platform.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_platform", kwargs={"pk": self.platform.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_platform(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_platform", kwargs={"pk": self.platform.pk})
        response = self.client.post(
            url, {"name": "AcmePlatform Renamed", "manufacturer": self.manufacturer.pk}
        )
        assert response.status_code == 302
        self.platform.refresh_from_db()
        assert self.platform.name == "AcmePlatform Renamed"

    def test_regular_user_post_does_not_update_platform(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_platform", kwargs={"pk": self.platform.pk})
        response = self.client.post(
            url, {"name": "AcmePlatform Renamed", "manufacturer": self.manufacturer.pk}
        )
        assert response.status_code == 403
        self.platform.refresh_from_db()
        assert self.platform.name == "AcmePlatform"


class DeletePlatformViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.platform = Platform.objects.create(
            name="AcmePlatform", manufacturer=manufacturer
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_platform", kwargs={"pk": self.platform.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_platform", kwargs={"pk": self.platform.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_platform", kwargs={"pk": self.platform.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_platform(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_platform", kwargs={"pk": self.platform.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Platform.objects.filter(pk=self.platform.pk).exists()

    def test_regular_user_post_does_not_delete_platform(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_platform", kwargs={"pk": self.platform.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert Platform.objects.filter(pk=self.platform.pk).exists()
