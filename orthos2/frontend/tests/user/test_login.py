from django.contrib.auth.models import User
from django.urls import reverse  # type: ignore
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
        form = self.app.get(reverse("frontend:login")).form  # type: ignore
        form["username"] = "user"
        form["password"] = "linux"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertEqual(page.context["user"].username, "user")  # type: ignore
        self.assertContains(page, "My Machine")  # type: ignore
        self.assertContains(page, "Logout")  # type: ignore

    def test_unsuccessful_user_login(self) -> None:
        """Test an unsuccessful user login."""
        form = self.app.get(reverse("frontend:login")).form  # type: ignore
        form["username"] = "user"
        form["password"] = "wrong"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertNotEqual(page.context["user"].username, "user")  # type: ignore
        self.assertNotContains(page, "My Machine")  # type: ignore
        self.assertContains(page, "Unknown login/password!")  # type: ignore

    def test_successful_superuser_login(self) -> None:
        """Test if a superuser can log in successfully."""
        form = self.app.get(reverse("frontend:login")).form  # type: ignore
        form["username"] = "superuser"
        form["password"] = "linux"
        page = form.submit().maybe_follow()  # type: ignore

        self.assertEqual(page.context["user"].username, "superuser")  # type: ignore
        self.assertContains(page, "My Machine")  # type: ignore
        self.assertContains(page, "All Machines")  # type: ignore

    def test_welcome_message(self) -> None:
        """Test if a welcome message shows up on the login page (if given)."""
        page = self.app.get(reverse("frontend:login"))  # type: ignore

        welcome_message = ServerConfig.get_server_config_manager().by_key(
            "orthos.web.welcomemessage"
        )

        self.assertContains(page, welcome_message)  # type: ignore

        message = ServerConfig.get_server_config_manager().get(
            key="orthos.web.welcomemessage"
        )
        message.value = ""
        message.save()
        page = self.app.get(reverse("frontend:login"))  # type: ignore

        self.assertNotContains(
            page,  # type: ignore
            welcome_message,  # type: ignore
        )

    def test_login_links(self) -> None:
        """Test all available links showing up on the login page."""
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            page = self.app.get(reverse("frontend:login"))  # type: ignore

            bugreport = ServerConfig.get_server_config_manager().by_key(
                "orthos.bugreport.url"
            )
            self.assertContains(page, "Bugreport")  # type: ignore
            self.assertContains(page, bugreport)  # type: ignore

            download_cli = ServerConfig.get_server_config_manager().by_key(
                "orthos.cli.url"
            )
            self.assertContains(page, "Download CLI")  # type: ignore
            self.assertContains(page, download_cli)  # type: ignore

            self.assertContains(page, "Login")  # type: ignore
            self.assertContains(page, "Create Account")  # type: ignore
            self.assertContains(page, "Restore Password")  # type: ignore

            self.assertNotContains(page, "Preferences")  # type: ignore
            self.assertNotContains(page, "Logout")  # type: ignore

    def test_login_with_password_free_user(self) -> None:
        """
        Migrated users have no password set. At the first login, users have to recover their
        password.
        """
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            form = self.app.get(reverse("frontend:login")).form  # type: ignore
            form["username"] = "user-nopassword"
            form["password"] = "linux"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertNotEqual(page.context["user"].username, "user-nopassword")  # type: ignore
            self.assertContains(page, "Please receive your initial password.")  # type: ignore
            self.assertIn("?user_id=", page.request.url)  # type: ignore

            form = page.form  # type: ignore
            form["email"] = "mail@wrong.de"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertContains(page, "E-Mail/login does not exist.")  # type: ignore

            form = page.form  # type: ignore
            form["login"] = "user-nopassword"
            form["email"] = "user-nopassword@foo.bar"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertContains(page, "Password restored - check your mails.")  # type: ignore
            self.assertNotEqual(page.context["user"].username, "user-nopassword")  # type: ignore
            self.assertIn(reverse("frontend:login"), page.request.url)  # type: ignore

            page = self.app.get(  # type: ignore
                reverse("frontend:free_machines"), user="user-nopassword"
            )

            self.assertEqual(page.context["user"].username, "user-nopassword")  # type: ignore

            # check for tasks
            self.assertEqual(SingleTask.objects.all().count(), 2)

            task_send_restored_password = SingleTask.objects.first()
            task_check_multiple_accounts = SingleTask.objects.last()

            user = User.objects.get(username="user-nopassword")

            if task_send_restored_password is None:
                self.fail("task_send_restored_password not set")
            self.assertEqual(
                task_send_restored_password.name,  # type: ignore
                "SendRestoredPassword",
            )
            self.assertIn(str(user.pk), task_send_restored_password.arguments)  # type: ignore
            if task_check_multiple_accounts is None:
                self.fail("task_check_multiple_accounts not set")
            self.assertEqual(
                task_check_multiple_accounts.name,  # type: ignore
                "CheckMultipleAccounts",
            )
            self.assertIn(str(user.pk), task_check_multiple_accounts.arguments)  # type: ignore
