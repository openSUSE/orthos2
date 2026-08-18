"""Tests for the SerialConsole CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Machine, SerialConsole, SerialConsoleType


class SerialConsoleViewTestCase(TestCase):
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def setUp(self) -> None:
        # "Device" type has no BMC dependency, unlike the fixture's "IPMI" type.
        self.device_type = SerialConsoleType.objects.create(
            name="Device", command="", comment="", has_ipmi_sol=False
        )
        # Machine pk=1 (cobbler.orthos2.test) has no serial console in the fixture.
        self.machine = Machine.objects.get(pk=1)


class SerialConsoleDetailViewTest(SerialConsoleViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:serialconsole", kwargs={"id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_authenticated_get_shows_not_configured(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:serialconsole", kwargs={"id": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"No serial console configured" in response.content


class NewSerialConsoleViewTest(SerialConsoleViewTestCase):
    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:new_serialconsole", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:new_serialconsole", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:new_serialconsole", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_serialconsole(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:new_serialconsole", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.post(
            url,
            {
                "stype": self.device_type.pk,
                "baud_rate": 57600,
                "kernel_device": "ttyS",
                "kernel_device_num": 0,
            },
        )
        assert response.status_code == 302
        assert SerialConsole.objects.filter(machine=self.machine).exists()

    def test_regular_user_post_does_not_create_serialconsole(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:new_serialconsole", kwargs={"machine_id": self.machine.pk}
        )
        response = self.client.post(
            url,
            {
                "stype": self.device_type.pk,
                "baud_rate": 57600,
                "kernel_device": "ttyS",
                "kernel_device_num": 0,
            },
        )
        assert response.status_code == 403
        assert not SerialConsole.objects.filter(machine=self.machine).exists()


class SerialConsoleDetailedEditViewTest(SerialConsoleViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.serialconsole = SerialConsole.objects.create(
            machine=self.machine,
            stype=self.device_type,
            baud_rate=57600,
            kernel_device="ttyS",
            kernel_device_num=0,
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_serialconsole(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.post(
            url,
            {
                "stype": self.device_type.pk,
                "baud_rate": 115200,
                "kernel_device": "ttyS",
                "kernel_device_num": 0,
            },
        )
        assert response.status_code == 302
        self.serialconsole.refresh_from_db()
        assert self.serialconsole.baud_rate == 115200

    def test_regular_user_post_does_not_update_serialconsole(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.post(
            url,
            {
                "stype": self.device_type.pk,
                "baud_rate": 115200,
                "kernel_device": "ttyS",
                "kernel_device_num": 0,
            },
        )
        assert response.status_code == 403
        self.serialconsole.refresh_from_db()
        assert self.serialconsole.baud_rate == 57600


class DeleteSerialConsoleViewTest(SerialConsoleViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.serialconsole = SerialConsole.objects.create(
            machine=self.machine,
            stype=self.device_type,
            baud_rate=57600,
            kernel_device="ttyS",
            kernel_device_num=0,
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_serialconsole(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not SerialConsole.objects.filter(machine=self.machine).exists()

    def test_regular_user_post_does_not_delete_serialconsole(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_serialconsole", kwargs={"pk": self.machine.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert SerialConsole.objects.filter(machine=self.machine).exists()
