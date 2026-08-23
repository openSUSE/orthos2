"""Tests for the superuser User create/edit/delete/deactivate frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from social_django.models import UserSocialAuth

from orthos2.taskmanager.models import SingleTask


class NewUserViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_user")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_user")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_user")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_user_with_unusable_password(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_user")
        response = self.client.post(
            url,
            {
                "username": "newperson",
                "email": "newperson@orthos2.test",
                "first_name": "New",
                "last_name": "Person",
                "is_active": "on",
            },
        )
        assert response.status_code == 302
        new_user = User.objects.get(username="newperson")
        assert not new_user.has_usable_password()

    def test_regular_user_post_does_not_create_user(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_user")
        response = self.client.post(url, {"username": "newperson"})
        assert response.status_code == 403
        assert not User.objects.filter(username="newperson").exists()


class UserDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.target = User.objects.create_user(
            username="targetuser", email="target@orthos2.test"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_user", kwargs={"pk": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_user", kwargs={"pk": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_user", kwargs={"pk": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_user(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_user", kwargs={"pk": self.target.pk})
        response = self.client.post(
            url,
            {
                "username": "targetuser",
                "email": "changed@orthos2.test",
                "first_name": "",
                "last_name": "",
                "is_active": "on",
                "is_staff": "on",
            },
        )
        assert response.status_code == 302
        self.target.refresh_from_db()
        assert self.target.email == "changed@orthos2.test"
        assert self.target.is_staff

    def test_regular_user_post_does_not_update_user(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_user", kwargs={"pk": self.target.pk})
        response = self.client.post(url, {"username": "targetuser", "is_staff": "on"})
        assert response.status_code == 403
        self.target.refresh_from_db()
        assert not self.target.is_staff


class DeleteUserViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.target = User.objects.create_user(username="targetuser")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_user", kwargs={"pk": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_user", kwargs={"pk": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_user", kwargs={"pk": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_user(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_user", kwargs={"pk": self.target.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not User.objects.filter(pk=self.target.pk).exists()

    def test_regular_user_post_does_not_delete_user(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_user", kwargs={"pk": self.target.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert User.objects.filter(pk=self.target.pk).exists()


class UserToggleActiveViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.target = User.objects.create_user(username="targetuser", is_active=True)

    def test_unauthenticated_post_redirects_to_login(self) -> None:
        url = reverse("frontend:user_toggle_active", kwargs={"id": self.target.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_post_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:user_toggle_active", kwargs={"id": self.target.pk})
        response = self.client.post(url)
        assert response.status_code == 403

    def test_superuser_post_deactivates_active_user(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:user_toggle_active", kwargs={"id": self.target.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        self.target.refresh_from_db()
        assert not self.target.is_active

    def test_superuser_post_reactivates_inactive_user(self) -> None:
        self.target.is_active = False
        self.target.save()
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:user_toggle_active", kwargs={"id": self.target.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        self.target.refresh_from_db()
        assert self.target.is_active


class UserSendPasswordResetViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.target = User.objects.create_user(username="targetuser")
        self.target.set_unusable_password()
        self.target.save()

    def test_unauthenticated_post_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:user_send_password_reset", kwargs={"id": self.target.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_post_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:user_send_password_reset", kwargs={"id": self.target.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 403

    def test_superuser_post_sets_usable_password_and_queues_email(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:user_send_password_reset", kwargs={"id": self.target.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        self.target.refresh_from_db()
        assert self.target.has_usable_password()
        assert SingleTask.objects.filter(name="SendRestoredPassword").exists()

    def test_superuser_post_is_blocked_for_oidc_linked_user(self) -> None:
        UserSocialAuth.objects.create(
            user=self.target, provider="oidc", uid="oidc-uid-1"
        )
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:user_send_password_reset", kwargs={"id": self.target.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        self.target.refresh_from_db()
        assert not self.target.has_usable_password()
        assert not SingleTask.objects.filter(name="SendRestoredPassword").exists()
