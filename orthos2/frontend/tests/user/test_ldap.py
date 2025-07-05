#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author Jan Löser <jan.loeser@posteo.de>
# Published under the GNU Public Licence 2

from django.urls import reverse  # type: ignore
from django_webtest import WebTest  # type: ignore

from orthos2.data.models.serverconfig import ServerConfig


class LDAP(WebTest):

    csrf_checks = True

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_enabled_user_creation(self) -> None:
        """
        Tests if user creation is enabled.
        """
        with self.settings(AUTH_ALLOW_USER_CREATION=True):
            page = self.app.get(reverse("frontend:login"))  # type: ignore
            self.assertContains(page, "Create Account")  # type: ignore
            self.assertContains(page, "Restore Password")  # type: ignore

    def test_disabled_user_creation(self) -> None:
        """
        Tests if user creation is disabled.
        """
        with self.settings(AUTH_ALLOW_USER_CREATION=False):
            creation = ServerConfig.get_server_config_manager().get(
                key="auth.account.creation"
            )
            creation.value = "bool:false"
            creation.save()

            page = self.app.get(reverse("frontend:login"))  # type: ignore
            self.assertNotContains(page, "Create Account")  # type: ignore
            self.assertNotContains(page, "Restore Password")  # type: ignore

            form = self.app.get(reverse("frontend:create_user")).form  # type: ignore
            form["login"] = "new-user"
            form["email"] = "new-user@example.com"
            form["password"] = "linux1234"
            form["password2"] = "linux1234"
            page = form.submit().maybe_follow()  # type: ignore

            self.assertNotEqual(page.context["user"].username, "new-user")  # type: ignore
            self.assertContains(page, "Account creation is disabled!")  # type: ignore
