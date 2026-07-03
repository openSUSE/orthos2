"""Tests for the DeleteNetworkInterface frontend view."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import NetworkInterface


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
