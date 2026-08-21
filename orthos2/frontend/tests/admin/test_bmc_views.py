"""Tests for the BMC CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import BMC, Machine, RemotePowerType


class BMCViewTestCase(TestCase):
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def setUp(self) -> None:
        self.fence_agent = RemotePowerType.objects.get(name="ipmilanplus")
        # Machine pk=1 (cobbler.orthos2.test) has a BMC ("my-bmc.foo.lan") in the fixture.
        self.machine = Machine.objects.get(pk=1)
        self.bmc = self.machine.bmc


class NewBMCViewTest(BMCViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.bmc.delete()

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_bmc", kwargs={"machine_id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_bmc", kwargs={"machine_id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_bmc", kwargs={"machine_id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_bmc(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_bmc", kwargs={"machine_id": self.machine.pk})
        response = self.client.post(
            url,
            {
                "fqdn": "new-bmc.orthos2.test",
                "mac": "AA:BB:CC:DD:EE:01",
                "username": "",
                "password": "",
                "fence_agent": self.fence_agent.pk,
            },
        )
        assert response.status_code == 302
        assert BMC.objects.filter(machine=self.machine).exists()
        # Creating a BMC auto-creates a matching remote power for the machine.
        self.machine.refresh_from_db()
        assert self.machine.has_remotepower()

    def test_regular_user_post_does_not_create_bmc(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_bmc", kwargs={"machine_id": self.machine.pk})
        response = self.client.post(
            url,
            {
                "fqdn": "new-bmc.orthos2.test",
                "mac": "AA:BB:CC:DD:EE:01",
                "username": "",
                "password": "",
                "fence_agent": self.fence_agent.pk,
            },
        )
        assert response.status_code == 403
        assert not BMC.objects.filter(machine=self.machine).exists()

    def test_superuser_post_username_without_password_shows_error(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_bmc", kwargs={"machine_id": self.machine.pk})
        response = self.client.post(
            url,
            {
                "fqdn": "new-bmc.orthos2.test",
                "mac": "AA:BB:CC:DD:EE:01",
                "username": "root",
                "password": "",
                "fence_agent": self.fence_agent.pk,
            },
        )
        assert response.status_code == 200
        assert not BMC.objects.filter(machine=self.machine).exists()


class BMCDetailedEditViewTest(BMCViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_bmc(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.post(
            url,
            {
                "fqdn": "edit-bmc.orthos2.test",
                "mac": "AA:BB:CC:DD:EE:03",
                "username": "",
                "password": "",
                "fence_agent": self.fence_agent.pk,
            },
        )
        assert response.status_code == 302
        self.bmc.refresh_from_db()
        assert self.bmc.mac == "AA:BB:CC:DD:EE:03"

    def test_regular_user_post_does_not_update_bmc(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.post(
            url,
            {
                "fqdn": "edit-bmc.orthos2.test",
                "mac": "AA:BB:CC:DD:EE:03",
                "username": "",
                "password": "",
                "fence_agent": self.fence_agent.pk,
            },
        )
        assert response.status_code == 403
        self.bmc.refresh_from_db()
        assert self.bmc.mac == ""


class DeleteBMCViewTest(BMCViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_bmc(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not BMC.objects.filter(pk=self.bmc.pk).exists()

    def test_regular_user_post_does_not_delete_bmc(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_bmc", kwargs={"pk": self.bmc.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert BMC.objects.filter(pk=self.bmc.pk).exists()
