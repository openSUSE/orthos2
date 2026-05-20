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
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""):
            form = self.app.get(reverse("frontend:login")).form  # type: ignore
            form["username"] = "user"
            form["password"] = "linux"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertEqual(page.context["user"].username, "user")  # type: ignore
            self.assertContains(page, "My Machine")  # type: ignore
            self.assertContains(page, "Logout")  # type: ignore

    def test_unsuccessful_user_login(self) -> None:
        """Test an unsuccessful user login."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""):
            form = self.app.get(reverse("frontend:login")).form  # type: ignore
            form["username"] = "user"
            form["password"] = "wrong"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertNotEqual(page.context["user"].username, "user")  # type: ignore
            self.assertNotContains(page, "My Machine")  # type: ignore
            self.assertContains(page, "Unknown login/password!")  # type: ignore

    def test_successful_superuser_login(self) -> None:
        """Test if a superuser can log in successfully."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""):
            form = self.app.get(reverse("frontend:login")).form  # type: ignore
            form["username"] = "superuser"
            form["password"] = "linux"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertEqual(page.context["user"].username, "superuser")  # type: ignore
            self.assertContains(page, "My Machine")  # type: ignore
            self.assertContains(page, "All Machines")  # type: ignore

    def test_welcome_message(self) -> None:
        """Test if a welcome message shows up on the login page (if given)."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""):
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
        with self.settings(
            AUTH_ALLOW_USER_CREATION=True, SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""
        ):
            page = self.app.get(reverse("frontend:login"))  # type: ignore

            bugreport = ServerConfig.get_server_config_manager().by_key(
                "orthos.bugreport.url"
            )
            self.assertContains(page, "Bugreport")  # type: ignore
            self.assertContains(page, bugreport)  # type: ignore

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
        with self.settings(
            AUTH_ALLOW_USER_CREATION=True, SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""
        ):
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


class LoginOIDCBehavior(WebTest):
    """Test login screen behavior with OIDC configuration."""

    csrf_checks = True

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_login_screen_without_oidc(self) -> None:
        """When OIDC is not configured, show built-in form normally."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""):
            page = self.app.get(reverse("frontend:login"))  # type: ignore

            # Should show built-in login form
            self.assertContains(page, 'name="username"')  # type: ignore
            self.assertContains(page, 'name="password"')  # type: ignore
            self.assertContains(page, 'type="submit"')  # type: ignore

    def test_login_screen_with_oidc_default(self) -> None:
        """When OIDC is configured, default screen shows only OIDC button."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT="https://auth.example.com"):
            page = self.app.get(reverse("frontend:login"))  # type: ignore

            # Should show OIDC button
            self.assertContains(page, "Login with Authentik")  # type: ignore

            # Should NOT show built-in form fields
            self.assertNotContains(page, 'name="username"')  # type: ignore
            self.assertNotContains(page, 'name="password"')  # type: ignore

            # Should NOT show link to builtin auth
            self.assertNotContains(page, "?builtin=true")  # type: ignore

    def test_login_screen_with_oidc_builtin_param(self) -> None:
        """When OIDC is configured but ?builtin=true, show built-in form."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT="https://auth.example.com"):
            page = self.app.get(reverse("frontend:login") + "?builtin=true")  # type: ignore

            # Should show built-in login form
            self.assertContains(page, 'name="username"')  # type: ignore
            self.assertContains(page, 'name="password"')  # type: ignore

            # Should show OIDC button as secondary option
            self.assertContains(page, "Login with Authentik")  # type: ignore

            # Should show warning message
            self.assertContains(page, "built-in authentication")  # type: ignore

    def test_builtin_login_works_with_oidc_enabled(self) -> None:
        """Verify built-in auth still functions when OIDC is configured."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT="https://auth.example.com"):
            page = self.app.get(reverse("frontend:login") + "?builtin=true")  # type: ignore
            form = page.form  # type: ignore
            form["username"] = "user"
            form["password"] = "linux"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertEqual(page.context["user"].username, "user")  # type: ignore
            self.assertContains(page, "My Machine")  # type: ignore

    def test_next_parameter_preserved_with_builtin(self) -> None:
        """Ensure ?next parameter works with ?builtin=true."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT="https://auth.example.com"):
            page = self.app.get(  # type: ignore
                reverse("frontend:login") + "?builtin=true&next=/machines/my"
            )
            form = page.form  # type: ignore
            form["username"] = "user"
            form["password"] = "linux"
            page = form.submit().maybe_follow()  # type: ignore

            # Should redirect correctly after login
            self.assertEqual(page.context["user"].username, "user")  # type: ignore

    def test_password_free_user_with_oidc_and_builtin(self) -> None:
        """Password-free user redirect should work with OIDC + builtin."""
        with self.settings(
            SOCIAL_AUTH_OIDC_OIDC_ENDPOINT="https://auth.example.com",
            AUTH_ALLOW_USER_CREATION=True,
        ):
            page = self.app.get(reverse("frontend:login") + "?builtin=true")  # type: ignore
            form = page.form  # type: ignore
            form["username"] = "user-nopassword"
            form["password"] = "linux"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertNotEqual(page.context["user"].username, "user-nopassword")  # type: ignore
            self.assertContains(page, "Please receive your initial password.")  # type: ignore
            self.assertIn("?user_id=", page.request.url)  # type: ignore

    def test_navbar_links_hidden_on_oidc_only_screen(self) -> None:
        """Create Account and Restore Password links hidden on OIDC-only screen."""
        with self.settings(
            SOCIAL_AUTH_OIDC_OIDC_ENDPOINT="https://auth.example.com",
            AUTH_ALLOW_USER_CREATION=True,
        ):
            page = self.app.get(reverse("frontend:login"))  # type: ignore

            # These links should not appear on OIDC-only screen
            self.assertNotContains(page, "Create Account")  # type: ignore
            self.assertNotContains(page, "Restore Password")  # type: ignore

    def test_navbar_links_visible_on_builtin_screen(self) -> None:
        """Create Account and Restore Password links appear on builtin screen."""
        with self.settings(
            SOCIAL_AUTH_OIDC_OIDC_ENDPOINT="https://auth.example.com",
            AUTH_ALLOW_USER_CREATION=True,
        ):
            page = self.app.get(reverse("frontend:login") + "?builtin=true")  # type: ignore

            # These links should appear on builtin screen
            self.assertContains(page, "Create Account")  # type: ignore
            self.assertContains(page, "Restore Password")  # type: ignore


class LoginOIDCBehaviorNoCSRF(WebTest):
    """Test login screen behavior with OIDC configuration."""

    csrf_checks = False

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_post_to_oidc_only_screen_ignored(self) -> None:
        """POST requests to OIDC-only screen should not process form."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT="https://auth.example.com"):
            # POST to OIDC-only screen (without builtin param)
            response = self.app.post(  # type: ignore
                reverse("frontend:login"),
                params={"username": "user", "password": "linux"},
            )

            # Should not log in the user
            # Should still show OIDC screen
            self.assertContains(response, "Login with Authentik")  # type: ignore


class RememberUsernameTests(WebTest):
    """Test the 'Remember username' feature."""

    csrf_checks = True

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_remember_username_checkbox_checked_sets_cookie(self) -> None:
        """When checkbox is checked, username should be stored in cookie."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""):
            form = self.app.get(reverse("frontend:login")).form  # type: ignore
            form["username"] = "user"
            form["password"] = "linux"
            form["remember_username"] = True
            response = form.submit()  # type: ignore

            self.assertIn("orthos2_remembered_username", response.test_app.cookies)  # type: ignore
            self.assertEqual(
                response.test_app.cookies["orthos2_remembered_username"], "user"  # type: ignore
            )

    def test_remember_username_checkbox_unchecked_no_cookie(self) -> None:
        """When checkbox is unchecked, no cookie should be set."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""):
            form = self.app.get(reverse("frontend:login")).form  # type: ignore
            form["username"] = "user"
            form["password"] = "linux"
            form["remember_username"] = False
            response = form.submit()  # type: ignore

            self.assertNotIn("orthos2_remembered_username", response.test_app.cookies)  # type: ignore

    def test_username_prefilled_from_cookie(self) -> None:
        """Username field should be pre-filled from existing cookie."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""):
            self.app.set_cookie("orthos2_remembered_username", "user")  # type: ignore

            page = self.app.get(reverse("frontend:login"))  # type: ignore
            form = page.form  # type: ignore

            # Username should be pre-filled
            self.assertEqual(form["username"].value, "user")  # type: ignore

    def test_cookie_deleted_when_checkbox_unchecked(self) -> None:
        """When user unchecks checkbox, cookie should be deleted."""
        with self.settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=""):
            # First login with remember checked
            form = self.app.get(reverse("frontend:login")).form  # type: ignore
            form["username"] = "user"
            form["password"] = "linux"
            form["remember_username"] = True
            form.submit()  # type: ignore

            # Logout - navigate to a page and submit the logout form
            page = self.app.get(reverse("frontend:free_machines"))  # type: ignore
            logout_form = page.forms["logout-form"]  # type: ignore
            logout_form.submit()  # type: ignore

            # Login again without remember
            form = self.app.get(reverse("frontend:login")).form  # type: ignore
            form["username"] = "user"
            form["password"] = "linux"
            form["remember_username"] = False
            response = form.submit()  # type: ignore

            self.assertNotIn("orthos2_remembered_username", response.test_app.cookies)  # type: ignore
