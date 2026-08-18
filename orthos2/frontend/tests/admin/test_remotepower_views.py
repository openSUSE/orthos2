"""Tests for the RemotePower CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Machine, RemotePower, RemotePowerDevice, RemotePowerType


class RemotePowerViewTestCase(TestCase):
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def setUp(self) -> None:
        # Machine pk=1 already has a remote power via RemotePowerDevice "apc" in the fixture.
        self.machine = Machine.objects.get(pk=1)
        self.remotepower = self.machine.remotepower
        self.remote_power_device = RemotePowerDevice.objects.get(
            fqdn="bmc.orthos2.test"
        )
        self.fence_agent = RemotePowerType.objects.get(name="apc")


class RemotePowerDetailViewTest(RemotePowerViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:remotepower", kwargs={"id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_authenticated_get_shows_configured_remotepower(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:remotepower", kwargs={"id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"apc" in response.content

    def test_authenticated_get_shows_not_configured(self) -> None:
        self.remotepower.delete()
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:remotepower", kwargs={"id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"No remote power configured" in response.content


class NewRemotePowerViewTest(RemotePowerViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.remotepower.delete()

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:new_remotepower", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:new_remotepower", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:new_remotepower", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_remotepower(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:new_remotepower", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.post(
            url,
            {
                "remote_power_device": self.remote_power_device.pk,
                "comment": "via rpower device",
                "options": "",
            },
        )
        assert response.status_code == 302
        assert RemotePower.objects.filter(machine=self.machine).exists()
        assert (
            RemotePower.objects.get(machine=self.machine).comment == "via rpower device"
        )

    def test_regular_user_post_does_not_create_remotepower(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:new_remotepower", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.post(
            url,
            {
                "remote_power_device": self.remote_power_device.pk,
                "comment": "via rpower device",
                "options": "",
            },
        )
        assert response.status_code == 403
        assert not RemotePower.objects.filter(machine=self.machine).exists()

    def test_superuser_post_with_invalid_port_shows_error(self) -> None:
        self.fence_agent.use_port = True
        self.fence_agent.save()

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:new_remotepower", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.post(
            url,
            {
                "remote_power_device": self.remote_power_device.pk,
                "port": "not-a-number",
                "options": "",
            },
        )
        assert response.status_code == 200
        assert not RemotePower.objects.filter(machine=self.machine).exists()


class RemotePowerDetailedEditViewTest(RemotePowerViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_remotepower(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.post(
            url,
            {
                "remote_power_device": self.remote_power_device.pk,
                "comment": "updated",
                "options": "",
            },
        )
        assert response.status_code == 302
        self.remotepower.refresh_from_db()
        assert self.remotepower.comment == "updated"

    def test_regular_user_post_does_not_update_remotepower(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.post(
            url,
            {
                "remote_power_device": self.remote_power_device.pk,
                "comment": "updated",
                "options": "",
            },
        )
        assert response.status_code == 403
        self.remotepower.refresh_from_db()
        assert self.remotepower.comment != "updated"


class DeleteRemotePowerViewTest(RemotePowerViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_remotepower(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not RemotePower.objects.filter(machine=self.machine).exists()

    def test_regular_user_post_does_not_delete_remotepower(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_remotepower", kwargs={"pk": self.machine.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert RemotePower.objects.filter(machine=self.machine).exists()
