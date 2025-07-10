from django.urls import reverse  # type: ignore
from django_webtest import WebTest  # type: ignore


class Statistics(WebTest):

    csrf_checks = True

    fixtures = []  # type: ignore

    def test_statistics_view(self) -> None:
        """Test if statistics view comes up."""
        page = self.app.get(reverse("frontend:free_machines"), user="user")  # type: ignore

        self.assertEqual(page.context["user"].username, "user")  # type: ignore

        page = page.click("Statistics").maybe_follow()  # type: ignore

        self.assertContains(page, "Numbers")  # type: ignore
