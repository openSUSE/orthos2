"""Tests for the Group CRUD frontend views."""

from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse


class GroupListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        Group.objects.create(name="Operators")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:groups")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:groups")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_groups(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:groups")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Operators" in response.content


class GroupDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.group = Group.objects.create(name="Operators")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:group_detail", kwargs={"id": self.group.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:group_detail", kwargs={"id": self.group.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:group_detail", kwargs={"id": self.group.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Operators" in response.content

    def test_nonexistent_group_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:group_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewGroupViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_group")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_group")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_group")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_group_with_permissions(self) -> None:
        permission = Permission.objects.first()
        assert permission is not None
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_group")
        response = self.client.post(
            url, {"name": "Operators", "permissions": [permission.pk]}
        )
        assert response.status_code == 302
        group = Group.objects.get(name="Operators")
        assert permission in group.permissions.all()

    def test_regular_user_post_does_not_create_group(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_group")
        response = self.client.post(url, {"name": "Operators"})
        assert response.status_code == 403
        assert not Group.objects.filter(name="Operators").exists()


class GroupDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.group = Group.objects.create(name="Operators")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_group", kwargs={"pk": self.group.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_group", kwargs={"pk": self.group.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_group", kwargs={"pk": self.group.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_group(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_group", kwargs={"pk": self.group.pk})
        response = self.client.post(url, {"name": "Operators Renamed"})
        assert response.status_code == 302
        self.group.refresh_from_db()
        assert self.group.name == "Operators Renamed"

    def test_regular_user_post_does_not_update_group(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_group", kwargs={"pk": self.group.pk})
        response = self.client.post(url, {"name": "Operators Renamed"})
        assert response.status_code == 403
        self.group.refresh_from_db()
        assert self.group.name == "Operators"


class DeleteGroupViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.group = Group.objects.create(name="Operators")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_group", kwargs={"pk": self.group.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_group", kwargs={"pk": self.group.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_group", kwargs={"pk": self.group.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_group(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_group", kwargs={"pk": self.group.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Group.objects.filter(pk=self.group.pk).exists()

    def test_regular_user_post_does_not_delete_group(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_group", kwargs={"pk": self.group.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert Group.objects.filter(pk=self.group.pk).exists()
