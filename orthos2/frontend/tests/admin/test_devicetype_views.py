"""Tests for the DeviceType CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import DeviceType, Manufacturer


class DeviceTypeListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        DeviceType.objects.create(name="AcmeDeviceType", manufacturer=manufacturer)

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:devicetypes")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:devicetypes")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_devicetypes(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:devicetypes")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeDeviceType" in response.content


class DeviceTypeDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=manufacturer
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:devicetype_detail", kwargs={"id": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:devicetype_detail", kwargs={"id": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:devicetype_detail", kwargs={"id": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeDeviceType" in response.content

    def test_nonexistent_devicetype_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:devicetype_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewDeviceTypeViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_devicetype")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_devicetype")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_devicetype")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_devicetype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_devicetype")
        response = self.client.post(
            url, {"name": "AcmeDeviceType", "manufacturer": self.manufacturer.pk}
        )
        assert response.status_code == 302
        assert DeviceType.objects.filter(name="AcmeDeviceType").exists()

    def test_regular_user_post_does_not_create_devicetype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_devicetype")
        response = self.client.post(
            url, {"name": "AcmeDeviceType", "manufacturer": self.manufacturer.pk}
        )
        assert response.status_code == 403
        assert not DeviceType.objects.filter(name="AcmeDeviceType").exists()


class DeviceTypeDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=self.manufacturer
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_devicetype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.post(
            url,
            {"name": "AcmeDeviceType Renamed", "manufacturer": self.manufacturer.pk},
        )
        assert response.status_code == 302
        self.devicetype.refresh_from_db()
        assert self.devicetype.name == "AcmeDeviceType Renamed"

    def test_regular_user_post_does_not_update_devicetype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.post(
            url,
            {"name": "AcmeDeviceType Renamed", "manufacturer": self.manufacturer.pk},
        )
        assert response.status_code == 403
        self.devicetype.refresh_from_db()
        assert self.devicetype.name == "AcmeDeviceType"


class DeleteDeviceTypeViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=manufacturer
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_devicetype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not DeviceType.objects.filter(pk=self.devicetype.pk).exists()

    def test_regular_user_post_does_not_delete_devicetype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert DeviceType.objects.filter(pk=self.devicetype.pk).exists()
