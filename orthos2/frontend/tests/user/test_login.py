from django.contrib.auth.models import User
from django.urls import reverse
from django_webtest import WebTest  # type: ignore

from orthos2.data.models import ServerConfig
from orthos2.taskmanager.models import SingleTask


class Login(WebTest):

    csrf_checks = True

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_successful_user_login(self) -> None:
        """Test if a user can log in successfully."""
        form = self.app.get(reverse("frontend:login")).form
        form["username"] = "user"
        form["password"] = "linux"
        page = form.submit().maybe_follow()

        self.assertEqual(page.context["user"].username, "user")
        self.assertContains(page, "My Machine")
        self.assertContains(page, "Logout")

    def test_unsuccessful_user_login(self) -> None:
        """Test an unsuccessful user login."""
        form = self.app.get(reverse("frontend:login")).form
        form["username"] = "user"
        form["password"] = "wrong"
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context["user"].username, "user")
        self.assertNotContains(page, "My Machine")
        self.assertContains(page, "Unknown login/password!")

    def test_successful_superuser_login(self) -> None:
        """Test if a superuser can log in successfully."""
        form = self.app.get(reverse("frontend:login")).form
        form["username"] = "superuser"
        form["password"] = "linux"
        page = form.submit().maybe_follow()

        self.assertEqual(page.context["user"].username, "superuser")
        self.assertContains(page, "My Machine")
        self.assertContains(page, "All Machines")

    def test_welcome_message(self) -> None:
        """Test if a welcome message shows up on the login page (if given)."""
        page = self.app.get(reverse("frontend:login"))

        welcome_message = ServerConfig.objects.by_key("orthos.web.welcomemessage")

        self.assertContains(page, welcome_message)

        message = ServerConfig.objects.get(key="orthos.web.welcomemessage")
        message.value = ""
        message.save()
        page = self.app.get(reverse("frontend:login"))

        self.assertNotContains(page, welcome_message)

    def test_login_links(self) -> None:
        """Test all available links showing up on the login page."""
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            page = self.app.get(reverse("frontend:login"))

            bugreport = ServerConfig.objects.by_key("orthos.bugreport.url")
            self.assertContains(page, "Bugreport")
            self.assertContains(page, bugreport)

            download_cli = ServerConfig.objects.by_key("orthos.cli.url")
            self.assertContains(page, "Download CLI")
            self.assertContains(page, download_cli)

            self.assertContains(page, "Login")
            self.assertContains(page, "Create Account")
            self.assertContains(page, "Restore Password")

            self.assertNotContains(page, "Preferences")
            self.assertNotContains(page, "Logout")

    def test_login_with_password_free_user(self) -> None:
        """
        Migrated users have no password set. At the first login, users have to recover their
        password.
        """
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            form = self.app.get(reverse("frontend:login")).form
            form["username"] = "user-nopassword"
            form["password"] = "linux"
            page = form.submit().maybe_follow()

            self.assertNotEqual(page.context["user"].username, "user-nopassword")
            self.assertContains(page, "Please receive your initial password.")
            self.assertIn("?user_id=", page.request.url)

            form = page.form
            form["email"] = "mail@wrong.de"
            page = form.submit().maybe_follow()

            self.assertContains(page, "E-Mail/login does not exist.")

            form = page.form
            form["login"] = "user-nopassword"
            form["email"] = "user-nopassword@foo.bar"
            page = form.submit().maybe_follow()

            self.assertContains(page, "Password restored - check your mails.")
            self.assertNotEqual(page.context["user"].username, "user-nopassword")
            self.assertIn(reverse("frontend:login"), page.request.url)

            page = self.app.get(
                reverse("frontend:free_machines"), user="user-nopassword"
            )

            self.assertEqual(page.context["user"].username, "user-nopassword")

            # check for tasks
            self.assertEqual(SingleTask.objects.all().count(), 2)

            task_send_restored_password = SingleTask.objects.first()
            task_check_multiple_accounts = SingleTask.objects.last()

            user = User.objects.get(username="user-nopassword")

            if task_send_restored_password is None:
                self.fail("task_send_restored_password not set")
            self.assertEqual(task_send_restored_password.name, "SendRestoredPassword")  # type: ignore
            self.assertIn(str(user.pk), task_send_restored_password.arguments)  # type: ignore
            if task_check_multiple_accounts is None:
                self.fail("task_check_multiple_accounts not set")
            self.assertEqual(task_check_multiple_accounts.name, "CheckMultipleAccounts")  # type: ignore
            self.assertIn(str(user.pk), task_check_multiple_accounts.arguments)  # type: ignore
