"""Tests for the Vendor CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Vendor


class VendorListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        Vendor.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:vendors")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:vendors")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_vendors(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:vendors")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeCorp" in response.content


class VendorDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.vendor = Vendor.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:vendor_detail", kwargs={"id": self.vendor.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:vendor_detail", kwargs={"id": self.vendor.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:vendor_detail", kwargs={"id": self.vendor.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeCorp" in response.content

    def test_nonexistent_vendor_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:vendor_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewVendorViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_vendor")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_vendor")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_vendor")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_vendor(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_vendor")
        response = self.client.post(url, {"name": "AcmeSubsidiary"})
        assert response.status_code == 302
        assert Vendor.objects.filter(name="AcmeSubsidiary").exists()

    def test_regular_user_post_does_not_create_vendor(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_vendor")
        response = self.client.post(url, {"name": "AcmeSubsidiary"})
        assert response.status_code == 403
        assert not Vendor.objects.filter(name="AcmeSubsidiary").exists()


class VendorDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.vendor = Vendor.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_vendor(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.post(url, {"name": "AcmeCorp Renamed"})
        assert response.status_code == 302
        self.vendor.refresh_from_db()
        assert self.vendor.name == "AcmeCorp Renamed"

    def test_regular_user_post_does_not_update_vendor(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.post(url, {"name": "AcmeCorp Renamed"})
        assert response.status_code == 403
        self.vendor.refresh_from_db()
        assert self.vendor.name == "AcmeCorp"


class DeleteVendorViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.vendor = Vendor.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_vendor(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Vendor.objects.filter(pk=self.vendor.pk).exists()

    def test_regular_user_post_does_not_delete_vendor(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_vendor", kwargs={"pk": self.vendor.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert Vendor.objects.filter(pk=self.vendor.pk).exists()
