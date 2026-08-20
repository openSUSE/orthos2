"""Tests for the ServerConfig CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import ServerConfig


class ServerConfigListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        ServerConfig.objects.create(key="acme.test.key", value="acme-value")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:serverconfigs")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:serverconfigs")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_serverconfigs(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:serverconfigs")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"acme.test.key" in response.content


class ServerConfigDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.serverconfig = ServerConfig.objects.create(
            key="acme.test.key", value="acme-value"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:serverconfig_detail", kwargs={"id": self.serverconfig.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:serverconfig_detail", kwargs={"id": self.serverconfig.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:serverconfig_detail", kwargs={"id": self.serverconfig.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"acme.test.key" in response.content

    def test_nonexistent_serverconfig_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:serverconfig_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewServerConfigViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_serverconfig")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_serverconfig")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_serverconfig")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_serverconfig(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_serverconfig")
        response = self.client.post(
            url, {"key": "acme.test.key", "value": "acme-value"}
        )
        assert response.status_code == 302
        assert ServerConfig.objects.filter(key="acme.test.key").exists()

    def test_regular_user_post_does_not_create_serverconfig(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_serverconfig")
        response = self.client.post(
            url, {"key": "acme.test.key", "value": "acme-value"}
        )
        assert response.status_code == 403
        assert not ServerConfig.objects.filter(key="acme.test.key").exists()


class ServerConfigDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.serverconfig = ServerConfig.objects.create(
            key="acme.test.key", value="acme-value"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_serverconfig", kwargs={"pk": self.serverconfig.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_serverconfig", kwargs={"pk": self.serverconfig.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_serverconfig", kwargs={"pk": self.serverconfig.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_serverconfig(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_serverconfig", kwargs={"pk": self.serverconfig.pk})
        response = self.client.post(url, {"key": "acme.test.key", "value": "new-value"})
        assert response.status_code == 302
        self.serverconfig.refresh_from_db()
        assert self.serverconfig.value == "new-value"

    def test_regular_user_post_does_not_update_serverconfig(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_serverconfig", kwargs={"pk": self.serverconfig.pk})
        response = self.client.post(url, {"key": "acme.test.key", "value": "new-value"})
        assert response.status_code == 403
        self.serverconfig.refresh_from_db()
        assert self.serverconfig.value == "acme-value"


class DeleteServerConfigViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.serverconfig = ServerConfig.objects.create(
            key="acme.test.key", value="acme-value"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:delete_serverconfig", kwargs={"pk": self.serverconfig.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_serverconfig", kwargs={"pk": self.serverconfig.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_serverconfig", kwargs={"pk": self.serverconfig.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_serverconfig(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_serverconfig", kwargs={"pk": self.serverconfig.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert not ServerConfig.objects.filter(pk=self.serverconfig.pk).exists()

    def test_regular_user_post_does_not_delete_serverconfig(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_serverconfig", kwargs={"pk": self.serverconfig.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 403
        assert ServerConfig.objects.filter(pk=self.serverconfig.pk).exists()
