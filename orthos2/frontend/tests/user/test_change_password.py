from django.contrib.auth.models import User
from django.urls import reverse
from django_webtest import WebTest  # type: ignore


class ChangePassword(WebTest):

    csrf_checks = True

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_successful_change_password(self) -> None:
        """Test if a new user can create an account."""
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            form = self.app.get(
                reverse("frontend:preferences_user"), user="user"
            ).forms[1]
            form["old_password"] = "linux"
            form["new_password"] = "linux1234"
            form["new_password2"] = "linux1234"
            page = form.submit().maybe_follow()

            self.assertEqual(page.context["user"].username, "user")
            self.assertIn(reverse("frontend:preferences_user"), page.request.url)
            self.assertContains(page, "Password successfully changed")

            user = User.objects.get(username="user")
            self.assertTrue(user.check_password("linux1234"))

    def test_wrong_current_password(self) -> None:
        """Check current (old) password."""
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            page = self.app.get(reverse("frontend:preferences_user"), user="user")
            form = page.forms[1]
            form["old_password"] = "wrongpassword"
            form["new_password"] = "linux1234"
            form["new_password2"] = "linux1234"
            page = form.submit().maybe_follow()

            self.assertEqual(page.context["user"].username, "user")
            self.assertIn(reverse("frontend:preferences_user"), page.request.url)
            self.assertContains(page, "Current password is wrong")

    def test_password_too_short(self) -> None:
        """Check if password is too short (at least 8 characters)."""
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            form = self.app.get(
                reverse("frontend:preferences_user"), user="user"
            ).forms[1]
            form["old_password"] = "linux"
            form["new_password"] = "1234"
            form["new_password2"] = "1234"
            page = form.submit().maybe_follow()

            self.assertEqual(page.context["user"].username, "user")
            self.assertIn(reverse("frontend:preferences_user"), page.request.url)
            self.assertContains(page, "Password is too short")

    def test_password_confirmation_not_match(self) -> None:
        """Check if passwords do match."""
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            form = self.app.get(
                reverse("frontend:preferences_user"), user="user"
            ).forms[1]
            form["old_password"] = "wrongpassword"
            form["new_password"] = "linux1234"
            form["new_password2"] = "1234linux"
            page = form.submit().maybe_follow()

            self.assertEqual(page.context["user"].username, "user")
            self.assertIn(reverse("frontend:preferences_user"), page.request.url)
            self.assertContains(page, "Password and confirmation password do not match")
