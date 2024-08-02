from django.urls import reverse
from django_webtest import WebTest


class Statistics(WebTest):

    csrf_checks = True

    fixtures = []

    def test_statistics_view(self):
        """Test if statistics view comes up."""
        page = self.app.get(reverse("frontend:free_machines"), user="user")

        self.assertEqual(page.context["user"].username, "user")

        page = page.click("Statistics").maybe_follow()

        self.assertContains(page, "Numbers")
