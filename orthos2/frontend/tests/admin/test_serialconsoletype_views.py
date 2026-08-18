"""Tests for the SerialConsoleType CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import SerialConsoleType


class SerialConsoleTypeListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        SerialConsoleType.objects.create(name="AcmeConsole")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:serialconsoletypes")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:serialconsoletypes")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_serialconsoletypes(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:serialconsoletypes")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeConsole" in response.content


class SerialConsoleTypeDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.serialconsoletype = SerialConsoleType.objects.create(name="AcmeConsole")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:serialconsoletype_detail",
            kwargs={"id": self.serialconsoletype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:serialconsoletype_detail",
            kwargs={"id": self.serialconsoletype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:serialconsoletype_detail",
            kwargs={"id": self.serialconsoletype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeConsole" in response.content

    def test_nonexistent_serialconsoletype_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:serialconsoletype_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewSerialConsoleTypeViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_serialconsoletype")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_serialconsoletype")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_serialconsoletype")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_serialconsoletype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_serialconsoletype")
        response = self.client.post(url, {"name": "AcmeConsole"})
        assert response.status_code == 302
        assert SerialConsoleType.objects.filter(name="AcmeConsole").exists()

    def test_regular_user_post_does_not_create_serialconsoletype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_serialconsoletype")
        response = self.client.post(url, {"name": "AcmeConsole"})
        assert response.status_code == 403
        assert not SerialConsoleType.objects.filter(name="AcmeConsole").exists()


class SerialConsoleTypeDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.serialconsoletype = SerialConsoleType.objects.create(name="AcmeConsole")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:edit_serialconsoletype", kwargs={"pk": self.serialconsoletype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_serialconsoletype", kwargs={"pk": self.serialconsoletype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_serialconsoletype", kwargs={"pk": self.serialconsoletype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_serialconsoletype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_serialconsoletype", kwargs={"pk": self.serialconsoletype.pk}
        )
        response = self.client.post(url, {"name": "AcmeConsole Renamed"})
        assert response.status_code == 302
        self.serialconsoletype.refresh_from_db()
        assert self.serialconsoletype.name == "AcmeConsole Renamed"

    def test_regular_user_post_does_not_update_serialconsoletype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_serialconsoletype", kwargs={"pk": self.serialconsoletype.pk}
        )
        response = self.client.post(url, {"name": "AcmeConsole Renamed"})
        assert response.status_code == 403
        self.serialconsoletype.refresh_from_db()
        assert self.serialconsoletype.name == "AcmeConsole"


class DeleteSerialConsoleTypeViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.serialconsoletype = SerialConsoleType.objects.create(name="AcmeConsole")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:delete_serialconsoletype",
            kwargs={"pk": self.serialconsoletype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_serialconsoletype",
            kwargs={"pk": self.serialconsoletype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_serialconsoletype",
            kwargs={"pk": self.serialconsoletype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_serialconsoletype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_serialconsoletype",
            kwargs={"pk": self.serialconsoletype.pk},
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert not SerialConsoleType.objects.filter(
            pk=self.serialconsoletype.pk
        ).exists()

    def test_regular_user_post_does_not_delete_serialconsoletype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_serialconsoletype",
            kwargs={"pk": self.serialconsoletype.pk},
        )
        response = self.client.post(url)
        assert response.status_code == 403
        assert SerialConsoleType.objects.filter(pk=self.serialconsoletype.pk).exists()
