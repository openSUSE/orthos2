from django.contrib.auth.models import User
from django.urls import reverse  # type: ignore
from django_webtest import WebTest  # type: ignore

from orthos2.taskmanager.models import SingleTask


class CreateAccount(WebTest):

    csrf_checks = True

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_successful_restore_password(self) -> None:
        """Test restore password functionality."""
        form = self.app.get(reverse("frontend:password_restore")).form  # type: ignore
        form["login"] = "user"
        form["email"] = "user@foo.bar"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "user")  # type: ignore
        self.assertIn(reverse("frontend:login"), page.request.url)  # type: ignore
        self.assertContains(page, "Password restored - check your mails")  # type: ignore

        # check for tasks
        self.assertEqual(SingleTask.objects.all().count(), 2)

        task_send_restored_password = SingleTask.objects.first()
        task_check_multiple_accounts = SingleTask.objects.last()

        user = User.objects.get(username="user")

        self.assertEqual(task_send_restored_password.name, "SendRestoredPassword")  # type: ignore
        self.assertIn(str(user.pk), task_send_restored_password.arguments)  # type: ignore
        self.assertEqual(task_check_multiple_accounts.name, "CheckMultipleAccounts")  # type: ignore
        self.assertIn(str(user.pk), task_check_multiple_accounts.arguments)  # type: ignore

    def test_unknown_login(self) -> None:
        """Check if login exists."""
        form = self.app.get(reverse("frontend:password_restore")).form  # type: ignore
        form["login"] = "unknown"
        form["email"] = "user@foo.bar"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "unknown")  # type: ignore
        self.assertIn(reverse("frontend:password_restore"), page.request.url)  # type: ignore
        self.assertContains(page, "E-Mail/login does not exist")  # type: ignore

    def test_unknown_email(self) -> None:
        """Check if email address exists."""
        form = self.app.get(reverse("frontend:password_restore")).form  # type: ignore
        form["login"] = "user"
        form["email"] = "unknown@unknown.foo"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "user")  # type: ignore
        self.assertIn(reverse("frontend:password_restore"), page.request.url)  # type: ignore
        self.assertContains(page, "E-Mail/login does not exist")  # type: ignore

    def test_invalid_email(self) -> None:
        """Check for valid email address."""
        form = self.app.get(reverse("frontend:password_restore")).form  # type: ignore
        form["login"] = "user"
        form["email"] = "user@invalid"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "user")  # type: ignore
        self.assertIn(reverse("frontend:password_restore"), page.request.url)  # type: ignore
        self.assertContains(page, "Enter a valid email address")  # type: ignore
