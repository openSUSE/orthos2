"""Tests for the DeleteNetworkInterface frontend view."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import BMC, NetworkInterface


class DeleteNetworkInterfaceViewTest(TestCase):
    """Tests for the networkinterface delete confirmation view."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_networkinterface", kwargs={"pk": 3})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        user = User.objects.get(username="user")
        self.client.force_login(user)
        url = reverse("frontend:delete_networkinterface", kwargs={"pk": 3})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)
        url = reverse("frontend:delete_networkinterface", kwargs={"pk": 3})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_secondary_interface(self) -> None:
        # NetworkInterface pk=3 is secondary (machine=2, primary=False)
        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)
        url = reverse("frontend:delete_networkinterface", kwargs={"pk": 3})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not NetworkInterface.objects.filter(pk=3).exists()

    def test_superuser_post_redirects_to_networkinterfaces(self) -> None:
        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)
        # NetworkInterface pk=3 belongs to machine pk=2
        url = reverse("frontend:delete_networkinterface", kwargs={"pk": 3})
        response = self.client.post(url)
        assert response.status_code == 302
        expected_url = reverse("frontend:networkinterfaces", kwargs={"id": 2})
        assert response.url == expected_url  # type: ignore[attr-defined]

    def test_superuser_post_primary_interface_is_forbidden(self) -> None:
        # NetworkInterface pk=1 is primary
        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)
        url = reverse("frontend:delete_networkinterface", kwargs={"pk": 1})
        response = self.client.post(url)
        assert response.status_code == 403
        assert NetworkInterface.objects.filter(pk=1).exists()

    def test_regular_user_post_is_forbidden(self) -> None:
        user = User.objects.get(username="user")
        self.client.force_login(user)
        url = reverse("frontend:delete_networkinterface", kwargs={"pk": 3})
        response = self.client.post(url)
        assert response.status_code == 403
        assert NetworkInterface.objects.filter(pk=3).exists()


class NewNetworkInterfaceViewTest(TestCase):
    """Tests for the new networkinterface view, scoped by machine."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_networkinterface", kwargs={"machine_id": 1})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_networkinterface", kwargs={"machine_id": 1})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_networkinterface", kwargs={"machine_id": 1})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_networkinterface(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_networkinterface", kwargs={"machine_id": 1})
        response = self.client.post(
            url,
            {
                "mac_address": "AA:BB:CC:DD:EE:AA",
                "ip_address_v4": "127.0.0.50",
            },
        )
        assert response.status_code == 302
        assert NetworkInterface.objects.filter(
            machine_id=1, mac_address="AA:BB:CC:DD:EE:AA"
        ).exists()

    def test_superuser_post_second_primary_is_rejected(self) -> None:
        # Machine pk=1 already has a primary interface (pk=1).
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_networkinterface", kwargs={"machine_id": 1})
        response = self.client.post(
            url,
            {
                "primary": "on",
                "mac_address": "AA:BB:CC:DD:EE:AB",
                "ip_address_v4": "127.0.0.51",
            },
        )
        assert response.status_code == 200
        assert not NetworkInterface.objects.filter(
            mac_address="AA:BB:CC:DD:EE:AB"
        ).exists()

    def test_superuser_post_mac_used_by_bmc_is_rejected(self) -> None:
        # BMC pk=1 (fixture) uses a specific MAC; reuse it here.
        bmc_mac = BMC.objects.get(pk=1).mac
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_networkinterface", kwargs={"machine_id": 1})
        response = self.client.post(
            url,
            {
                "mac_address": bmc_mac,
                "ip_address_v4": "127.0.0.52",
            },
        )
        assert response.status_code == 200
        assert not NetworkInterface.objects.filter(
            machine_id=1, mac_address=bmc_mac
        ).exists()

    def test_regular_user_post_does_not_create_networkinterface(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_networkinterface", kwargs={"machine_id": 1})
        response = self.client.post(
            url,
            {
                "mac_address": "AA:BB:CC:DD:EE:AC",
                "ip_address_v4": "127.0.0.53",
            },
        )
        assert response.status_code == 403
        assert not NetworkInterface.objects.filter(
            mac_address="AA:BB:CC:DD:EE:AC"
        ).exists()


class NetworkInterfaceDetailedEditViewTest(TestCase):
    """Tests for the networkinterface edit view."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_networkinterface", kwargs={"pk": 3})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_networkinterface", kwargs={"pk": 3})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_networkinterface", kwargs={"pk": 3})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_networkinterface(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_networkinterface", kwargs={"pk": 3})
        response = self.client.post(
            url,
            {
                "mac_address": "CA:FE:BE:EF:C0:DE",
                "ip_address_v4": "127.0.0.60",
            },
        )
        assert response.status_code == 302
        interface = NetworkInterface.objects.get(pk=3)
        assert interface.ip_address_v4 == "127.0.0.60"

    def test_regular_user_post_does_not_update_networkinterface(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_networkinterface", kwargs={"pk": 3})
        response = self.client.post(
            url,
            {
                "mac_address": "CA:FE:BE:EF:C0:DE",
                "ip_address_v4": "127.0.0.61",
            },
        )
        assert response.status_code == 403
        interface = NetworkInterface.objects.get(pk=3)
        assert interface.ip_address_v4 == "127.0.0.11"
