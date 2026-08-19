"""Tests for the Manufacturer CRUD frontend views."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Manufacturer
from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionRun


class ManufacturerListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:manufacturers")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_lists_manufacturers(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:manufacturers")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeCorp" in response.content

    def test_superuser_get_lists_manufacturers(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:manufacturers")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeCorp" in response.content

    def test_search_by_name(self) -> None:
        Manufacturer.objects.create(name="OtherCorp")
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(reverse("frontend:manufacturers"), {"query": "Acme"})
        assert b"AcmeCorp" in response.content
        assert b"OtherCorp" not in response.content

    def test_quick_filter_has_netbox_yes(self) -> None:
        Manufacturer.objects.create(name="LinkedCorp", netbox_id=7)
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(
            reverse("frontend:manufacturers"), {"has_netbox": "1"}
        )
        assert b"LinkedCorp" in response.content
        assert b"AcmeCorp" not in response.content

    def test_quick_filter_has_netbox_no(self) -> None:
        Manufacturer.objects.create(name="LinkedCorp", netbox_id=7)
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(
            reverse("frontend:manufacturers"), {"has_netbox": "0"}
        )
        assert b"AcmeCorp" in response.content
        assert b"LinkedCorp" not in response.content


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

    def test_regular_user_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:manufacturer_detail", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeCorp" in response.content

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
        response = self.client.post(url, {"name": "AcmeSubsidiary", "netbox_id": 0})
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
        response = self.client.post(url, {"name": "AcmeCorp Renamed", "netbox_id": 0})
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

    def test_name_field_disabled_once_netbox_id_is_set(self) -> None:
        self.manufacturer.netbox_id = 42
        self.manufacturer.save()
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_manufacturer", kwargs={"pk": self.manufacturer.pk})
        response = self.client.get(url)
        assert response.context["form"].fields["name"].disabled

    def test_name_field_enabled_when_netbox_id_is_unset(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_manufacturer", kwargs={"pk": self.manufacturer.pk})
        response = self.client.get(url)
        assert not response.context["form"].fields["name"].disabled

    def test_name_change_is_ignored_once_netbox_id_is_set(self) -> None:
        self.manufacturer.netbox_id = 42
        self.manufacturer.save()
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_manufacturer", kwargs={"pk": self.manufacturer.pk})
        response = self.client.post(url, {"name": "Should Not Apply", "netbox_id": 42})
        assert response.status_code == 302
        self.manufacturer.refresh_from_db()
        assert self.manufacturer.name == "AcmeCorp"


class ManufacturerPlatformsViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:manufacturer_platforms", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_can_view_platforms(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:manufacturer_platforms", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200


class ManufacturerFetchNetboxViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp", netbox_id=42)

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:manufacturer_netbox_fetch", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:manufacturer_netbox_fetch", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_queues_fetch_task(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:manufacturer_netbox_fetch", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302


class ManufacturerCompareNetboxViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp", netbox_id=42)

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:manufacturer_netbox_compare", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:manufacturer_netbox_compare", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_queues_compare_task(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:manufacturer_netbox_compare", kwargs={"id": self.manufacturer.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302


class ManufacturerNetboxComparisonViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp", netbox_id=42)

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:manufacturer_netbox_comparisons",
            kwargs={"id": self.manufacturer.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_can_view_with_no_runs_yet(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:manufacturer_netbox_comparisons",
            kwargs={"id": self.manufacturer.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_regular_user_sees_latest_run(self) -> None:
        with patch.object(
            self.manufacturer,
            "fetch_netbox_record",
            return_value={"name": "AcmeCorp", "description": "from netbox"},
        ):
            self.manufacturer.compare_netbox()

        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:manufacturer_netbox_comparisons",
            kwargs={"id": self.manufacturer.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        run = NetboxOrthosComparisionRun.objects.get(
            object_manufacturer=self.manufacturer
        )
        assert response.context["manufacturer_run"] == run


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
