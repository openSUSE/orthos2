"""Tests for the RemotePowerType CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import RemotePowerType


class RemotePowerTypeListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        RemotePowerType.objects.create(name="AcmeRemotePowerType")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_remotepowertypes(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeRemotePowerType" in response.content


class RemotePowerTypeDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:remotepowertype_detail",
            kwargs={"id": self.remotepowertype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:remotepowertype_detail",
            kwargs={"id": self.remotepowertype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:remotepowertype_detail",
            kwargs={"id": self.remotepowertype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeRemotePowerType" in response.content

    def test_nonexistent_remotepowertype_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertype_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewRemotePowerTypeViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_remotepowertype")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_remotepowertype")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_remotepowertype")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_remotepowertype")
        response = self.client.post(
            url,
            {"name": "AcmeRemotePowerType", "device": "bmc"},
        )
        assert response.status_code == 302
        assert RemotePowerType.objects.filter(name="AcmeRemotePowerType").exists()

    def test_regular_user_post_does_not_create_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_remotepowertype")
        response = self.client.post(
            url,
            {"name": "AcmeRemotePowerType", "device": "bmc"},
        )
        assert response.status_code == 403
        assert not RemotePowerType.objects.filter(name="AcmeRemotePowerType").exists()


class RemotePowerTypeDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.post(
            url,
            {"name": "AcmeRemotePowerType Renamed", "device": "bmc"},
        )
        assert response.status_code == 302
        self.remotepowertype.refresh_from_db()
        assert self.remotepowertype.name == "AcmeRemotePowerType Renamed"

    def test_regular_user_post_does_not_update_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.post(
            url,
            {"name": "AcmeRemotePowerType Renamed", "device": "bmc"},
        )
        assert response.status_code == 403
        self.remotepowertype.refresh_from_db()
        assert self.remotepowertype.name == "AcmeRemotePowerType"


class DeleteRemotePowerTypeViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert not RemotePowerType.objects.filter(pk=self.remotepowertype.pk).exists()

    def test_regular_user_post_does_not_delete_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 403
        assert RemotePowerType.objects.filter(pk=self.remotepowertype.pk).exists()
