from django.urls import reverse  # type: ignore
from django_webtest import WebTest  # type: ignore


class Logout(WebTest):

    csrf_checks = True

    fixtures = [
        "orthos2/frontend/tests/fixtures/serverconfigs.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_successful_logout(self) -> None:
        """Test if a user can log out successfully."""
        # Arrange
        page = self.app.get(reverse("frontend:free_machines"), user="user")  # type: ignore

        # Assert user is logged in
        self.assertEqual(page.context["user"].username, "user")  # type: ignore

        # Act
        logout_form = page.forms[0]  # type: ignore
        res = logout_form.submit("Logout").maybe_follow()  # type: ignore

        # Assert
        self.assertContains(res, "Login")  # type: ignore
