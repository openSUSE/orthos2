from django.urls import reverse  # type: ignore
from django_webtest import WebTest  # type: ignore


class CreateAccount(WebTest):

    csrf_checks = True

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_successful_user_creation(self) -> None:
        """Test if a new user can create an account."""
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            form = self.app.get(reverse("frontend:create_user")).form  # type: ignore
            form["login"] = "new-user"
            form["email"] = "new-user@foo.bar"
            form["password"] = "linux1234"
            form["password2"] = "linux1234"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertEqual(page.context["user"].username, "new-user")  # type: ignore
            self.assertIn(reverse("frontend:machines"), page.request.url)  # type: ignore
            self.assertContains(page, "My Machine")  # type: ignore

    def test_password_too_short(self) -> None:
        """Check if password is too short (at least 8 characters)."""
        form = self.app.get(reverse("frontend:create_user")).form  # type: ignore
        form["login"] = "new-user"
        form["email"] = "new-user@foo.bar"
        form["password"] = "1234567"
        form["password2"] = "1234567"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "new-user")  # type: ignore
        self.assertIn(reverse("frontend:create_user"), page.request.url)  # type: ignore
        self.assertContains(page, "Password is too short")  # type: ignore

    def test_password_confirmation_not_match(self) -> None:
        """Check if passwords do match."""
        form = self.app.get(reverse("frontend:create_user")).form  # type: ignore
        form["login"] = "new-user"
        form["email"] = "new-user@foo.bar"
        form["password"] = "123456789"
        form["password2"] = "123456798"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "new-user")  # type: ignore
        self.assertIn(reverse("frontend:create_user"), page.request.url)  # type: ignore
        self.assertContains(page, "Password and confirmation password do not match")  # type: ignore

    def test_user_already_exists(self) -> None:
        """Check if user does already exists."""
        form = self.app.get(reverse("frontend:create_user")).form  # type: ignore
        form["login"] = "user"
        form["email"] = "user@foo.bar"
        form["password"] = "12345678"
        form["password2"] = "12345678"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "user")  # type: ignore
        self.assertIn(reverse("frontend:create_user"), page.request.url)  # type: ignore
        self.assertContains(page, "does already exist")  # type: ignore

    def test_email_does_already_exists(self) -> None:
        """Check if email does already exists."""
        form = self.app.get(reverse("frontend:create_user")).form  # type: ignore
        form["login"] = "new-user"
        form["email"] = "user@foo.bar"
        form["password"] = "12345678"
        form["password2"] = "12345678"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "user")  # type: ignore
        self.assertIn(reverse("frontend:create_user"), page.request.url)  # type: ignore
        self.assertContains(page, "is already in use")  # type: ignore

    def test_invalid_email(self) -> None:
        """Check for valid email address."""
        form = self.app.get(reverse("frontend:create_user")).form  # type: ignore
        form["login"] = "new-user"
        form["email"] = "new-user@invalid"
        form["password"] = "12345678"
        form["password2"] = "12345678"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "user")  # type: ignore
        self.assertIn(reverse("frontend:create_user"), page.request.url)  # type: ignore
        self.assertContains(page, "Enter a valid email address")  # type: ignore
