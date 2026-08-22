"""Tests for the RemotePowerDevice CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import (
    Architecture,
    Domain,
    Machine,
    RemotePower,
    RemotePowerDevice,
    RemotePowerType,
    ServerConfig,
    System,
)


class RemotePowerDeviceViewTestCase(TestCase):
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
        self.fence_agent = RemotePowerType.objects.create(
            name="AcmeFenceAgent", device="rpowerdevice"
        )
        self.remotepowerdevice = RemotePowerDevice.objects.create(
            fqdn="rpower.orthos2.test",
            mac="AA:BB:CC:DD:EE:FF",
            fence_agent=self.fence_agent,
            architecture=self.architecture,
            domain=self.domain,
        )


class RemotePowerDevicesListViewTest(RemotePowerDeviceViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:remotepowerdevices")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:remotepowerdevices")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_remotepowerdevices(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowerdevices")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"rpower.orthos2.test" in response.content

    def test_superuser_get_shows_machine_count(self) -> None:
        other_device = RemotePowerDevice.objects.create(
            fqdn="other-rpower.orthos2.test",
            mac="AA:BB:CC:DD:EE:00",
            fence_agent=self.fence_agent,
            architecture=self.architecture,
            domain=self.domain,
        )
        machine = Machine.objects.create(
            fqdn="powered-machine.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=self.architecture,
        )
        RemotePower.objects.create(
            machine=machine, remote_power_device=self.remotepowerdevice
        )

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowerdevices")
        response = self.client.get(url)
        listed = {
            remotepowerdevice.pk: remotepowerdevice
            for remotepowerdevice in response.context["object_list"]
        }
        assert listed[self.remotepowerdevice.pk].machine_count == 1
        assert listed[other_device.pk].machine_count == 0


class RemotePowerDeviceDetailViewTest(RemotePowerDeviceViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:remotepowerdevice_detail",
            kwargs={"id": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_redirects_to_login(self) -> None:
        # remotepowerdevice_detail is gated by the bare @permission_required
        # decorator, which redirects rather than raises PermissionDenied
        # for authenticated users lacking the permission.
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:remotepowerdevice_detail",
            kwargs={"id": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:remotepowerdevice_detail",
            kwargs={"id": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"rpower.orthos2.test" in response.content

    def test_nonexistent_remotepowerdevice_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowerdevice_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class RemotePowerDeviceMachinesViewTest(RemotePowerDeviceViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.machine = Machine.objects.create(
            fqdn="powered-machine.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=self.architecture,
        )
        RemotePower.objects.create(
            machine=self.machine, remote_power_device=self.remotepowerdevice
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:remotepowerdevice_machines",
            kwargs={"id": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_redirects_to_login(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:remotepowerdevice_machines",
            kwargs={"id": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_superuser_get_lists_machines_using_this_device(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:remotepowerdevice_machines",
            kwargs={"id": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"powered-machine.orthos2.test" in response.content

    def test_nonexistent_remotepowerdevice_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowerdevice_machines", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewRemotePowerDeviceViewTest(RemotePowerDeviceViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_remotepowerdevice")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_remotepowerdevice")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_remotepowerdevice")
        response = self.client.get(url)
        assert response.status_code == 200


class RemotePowerDeviceDetailedEditViewTest(RemotePowerDeviceViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:edit_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_remotepowerdevice(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.post(
            url,
            {
                "fqdn": "rpower.orthos2.test",
                "netbox_id": 0,
                "username": "newuser",
                "password": "newpass",
                "url": "",
            },
        )
        assert response.status_code == 302
        self.remotepowerdevice.refresh_from_db()
        assert self.remotepowerdevice.username == "newuser"

    def test_regular_user_post_does_not_update_remotepowerdevice(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.post(
            url,
            {
                "fqdn": "rpower.orthos2.test",
                "netbox_id": 0,
                "username": "newuser",
                "password": "newpass",
                "url": "",
            },
        )
        assert response.status_code == 403
        self.remotepowerdevice.refresh_from_db()
        assert self.remotepowerdevice.username != "newuser"


class DeleteRemotePowerDeviceViewTest(RemotePowerDeviceViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:delete_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_remotepowerdevice(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert not RemotePowerDevice.objects.filter(
            pk=self.remotepowerdevice.pk
        ).exists()

    def test_regular_user_post_does_not_delete_remotepowerdevice(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_remotepowerdevice",
            kwargs={"pk": self.remotepowerdevice.pk},
        )
        response = self.client.post(url)
        assert response.status_code == 403
        assert RemotePowerDevice.objects.filter(pk=self.remotepowerdevice.pk).exists()


class RemotePowerDeviceNetboxComparisonViewTest(RemotePowerDeviceViewTestCase):
    def test_regular_user_get_is_redirected_with_error(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:remotepowerdevice_netbox_comparisons",
            kwargs={"id": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302

    def test_superuser_get_shows_comparison_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:remotepowerdevice_netbox_comparisons",
            kwargs={"id": self.remotepowerdevice.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200
