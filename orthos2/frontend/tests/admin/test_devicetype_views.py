"""Tests for the DeviceType CRUD frontend views."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import DeviceType, Manufacturer
from orthos2.data.models.netboxorthoscomparision import NetboxOrthosComparisionRun
from orthos2.taskmanager.models import SingleTask


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

    def test_regular_user_get_lists_devicetypes(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:devicetypes")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeDeviceType" in response.content

    def test_superuser_get_lists_devicetypes(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:devicetypes")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeDeviceType" in response.content

    def test_search_by_name(self) -> None:
        manufacturer = Manufacturer.objects.create(name="OtherCorp")
        DeviceType.objects.create(name="OtherDeviceType", manufacturer=manufacturer)
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(reverse("frontend:devicetypes"), {"query": "Acme"})
        assert b"AcmeDeviceType" in response.content
        assert b"OtherDeviceType" not in response.content

    def test_quick_filter_has_netbox_yes(self) -> None:
        manufacturer = Manufacturer.objects.create(name="OtherCorp")
        DeviceType.objects.create(
            name="LinkedDeviceType", manufacturer=manufacturer, netbox_id=7
        )
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(reverse("frontend:devicetypes"), {"has_netbox": "1"})
        assert b"LinkedDeviceType" in response.content
        assert b"AcmeDeviceType" not in response.content

    def test_quick_filter_has_netbox_no(self) -> None:
        manufacturer = Manufacturer.objects.create(name="OtherCorp")
        DeviceType.objects.create(
            name="LinkedDeviceType", manufacturer=manufacturer, netbox_id=7
        )
        self.client.force_login(User.objects.get(username="user"))
        response = self.client.get(reverse("frontend:devicetypes"), {"has_netbox": "0"})
        assert b"AcmeDeviceType" in response.content
        assert b"LinkedDeviceType" not in response.content


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

    def test_regular_user_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:devicetype_detail", kwargs={"id": self.devicetype.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeDeviceType" in response.content

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
            url,
            {
                "name": "AcmeDeviceType",
                "manufacturer": self.manufacturer.pk,
                "netbox_id": 0,
            },
        )
        assert response.status_code == 302
        assert DeviceType.objects.filter(name="AcmeDeviceType").exists()

    def test_regular_user_post_does_not_create_devicetype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_devicetype")
        response = self.client.post(
            url,
            {
                "name": "AcmeDeviceType",
                "manufacturer": self.manufacturer.pk,
                "netbox_id": 0,
            },
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
            {
                "name": "AcmeDeviceType Renamed",
                "manufacturer": self.manufacturer.pk,
                "netbox_id": 0,
            },
        )
        assert response.status_code == 302
        self.devicetype.refresh_from_db()
        assert self.devicetype.name == "AcmeDeviceType Renamed"

    def test_regular_user_post_does_not_update_devicetype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.post(
            url,
            {
                "name": "AcmeDeviceType Renamed",
                "manufacturer": self.manufacturer.pk,
                "netbox_id": 0,
            },
        )
        assert response.status_code == 403
        self.devicetype.refresh_from_db()
        assert self.devicetype.name == "AcmeDeviceType"

    def test_name_field_disabled_once_netbox_id_is_set(self) -> None:
        self.devicetype.netbox_id = 42
        self.devicetype.save()
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.get(url)
        assert response.context["form"].fields["name"].disabled

    def test_name_field_enabled_when_netbox_id_is_unset(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.get(url)
        assert not response.context["form"].fields["name"].disabled

    def test_name_change_is_ignored_once_netbox_id_is_set(self) -> None:
        self.devicetype.netbox_id = 42
        self.devicetype.save()
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_devicetype", kwargs={"pk": self.devicetype.pk})
        response = self.client.post(
            url,
            {
                "name": "Should Not Apply",
                "manufacturer": self.manufacturer.pk,
                "netbox_id": 42,
            },
        )
        assert response.status_code == 302
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


class DeviceTypeFetchNetboxViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=manufacturer, netbox_id=42
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:devicetype_netbox_fetch", kwargs={"id": self.devicetype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:devicetype_netbox_fetch", kwargs={"id": self.devicetype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_queues_fetch_task(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:devicetype_netbox_fetch", kwargs={"id": self.devicetype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302

    def test_superuser_get_when_not_synced_does_not_queue_task(self) -> None:
        manufacturer = Manufacturer.objects.create(name="OtherCorp")
        unsynced = DeviceType.objects.create(
            name="UnsyncedDeviceType", manufacturer=manufacturer
        )
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:devicetype_netbox_fetch", kwargs={"id": unsynced.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert not SingleTask.objects.filter(name="NetboxFetchFullDeviceType").exists()


class DeviceTypeCompareNetboxViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=manufacturer, netbox_id=42
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:devicetype_netbox_compare", kwargs={"id": self.devicetype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:devicetype_netbox_compare", kwargs={"id": self.devicetype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_queues_compare_task(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:devicetype_netbox_compare", kwargs={"id": self.devicetype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302

    def test_superuser_get_when_not_synced_does_not_queue_task(self) -> None:
        manufacturer = Manufacturer.objects.create(name="OtherCorp")
        unsynced = DeviceType.objects.create(
            name="UnsyncedDeviceType", manufacturer=manufacturer
        )
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:devicetype_netbox_compare", kwargs={"id": unsynced.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert not SingleTask.objects.filter(name="NetboxCompareDeviceType").exists()


class DeviceTypeNetboxComparisonViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        manufacturer = Manufacturer.objects.create(name="AcmeCorp")
        self.devicetype = DeviceType.objects.create(
            name="AcmeDeviceType", manufacturer=manufacturer, netbox_id=42
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:devicetype_netbox_comparisons",
            kwargs={"id": self.devicetype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_can_view_with_no_runs_yet(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:devicetype_netbox_comparisons",
            kwargs={"id": self.devicetype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_regular_user_sees_latest_run(self) -> None:
        with patch.object(
            self.devicetype,
            "fetch_netbox_record",
            return_value={"model": "AcmeDeviceType", "description": "from netbox"},
        ):
            self.devicetype.compare_netbox()

        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:devicetype_netbox_comparisons",
            kwargs={"id": self.devicetype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        run = NetboxOrthosComparisionRun.objects.get(object_device_type=self.devicetype)
        assert response.context["devicetype_run"] == run
