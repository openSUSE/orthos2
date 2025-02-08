from django.urls import reverse
from django_webtest import WebTest  # type: ignore


class Statistics(WebTest):

    csrf_checks = True

    fixtures = []  # type: ignore

    def test_statistics_view(self) -> None:
        """Test if statistics view comes up."""
        page = self.app.get(reverse("frontend:free_machines"), user="user")

        self.assertEqual(page.context["user"].username, "user")

        page = page.click("Statistics").maybe_follow()

        self.assertContains(page, "Numbers")
