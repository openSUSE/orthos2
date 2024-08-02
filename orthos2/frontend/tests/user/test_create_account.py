from django.urls import reverse
from django_webtest import WebTest


class CreateAccount(WebTest):

    csrf_checks = True

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_successful_user_creation(self):
        """Test if a new user can create an account."""
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            form = self.app.get(reverse("frontend:create_user")).form
            form["login"] = "new-user"
            form["email"] = "new-user@foo.bar"
            form["password"] = "linux1234"
            form["password2"] = "linux1234"
            page = form.submit().maybe_follow()

            self.assertEqual(page.context["user"].username, "new-user")
            self.assertIn(reverse("frontend:machines"), page.request.url)
            self.assertContains(page, "My Machine")

    def test_password_too_short(self):
        """Check if password is too short (at least 8 characters)."""
        form = self.app.get(reverse("frontend:create_user")).form
        form["login"] = "new-user"
        form["email"] = "new-user@foo.bar"
        form["password"] = "1234567"
        form["password2"] = "1234567"
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context["user"].username, "new-user")
        self.assertIn(reverse("frontend:create_user"), page.request.url)
        self.assertContains(page, "Password is too short")

    def test_password_confirmation_not_match(self):
        """Check if passwords do match."""
        form = self.app.get(reverse("frontend:create_user")).form
        form["login"] = "new-user"
        form["email"] = "new-user@foo.bar"
        form["password"] = "123456789"
        form["password2"] = "123456798"
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context["user"].username, "new-user")
        self.assertIn(reverse("frontend:create_user"), page.request.url)
        self.assertContains(page, "Password and confirmation password do not match")

    def test_user_already_exists(self):
        """Check if user does already exists."""
        form = self.app.get(reverse("frontend:create_user")).form
        form["login"] = "user"
        form["email"] = "user@foo.bar"
        form["password"] = "12345678"
        form["password2"] = "12345678"
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context["user"].username, "user")
        self.assertIn(reverse("frontend:create_user"), page.request.url)
        self.assertContains(page, "does already exist")

    def test_email_does_already_exists(self):
        """Check if email does already exists."""
        form = self.app.get(reverse("frontend:create_user")).form
        form["login"] = "new-user"
        form["email"] = "user@foo.bar"
        form["password"] = "12345678"
        form["password2"] = "12345678"
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context["user"].username, "user")
        self.assertIn(reverse("frontend:create_user"), page.request.url)
        self.assertContains(page, "is already in use")

    def test_invalid_email(self):
        """Check for valid email address."""
        form = self.app.get(reverse("frontend:create_user")).form
        form["login"] = "new-user"
        form["email"] = "new-user@invalid"
        form["password"] = "12345678"
        form["password2"] = "12345678"
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context["user"].username, "user")
        self.assertIn(reverse("frontend:create_user"), page.request.url)
        self.assertContains(page, "Enter a valid email address")
