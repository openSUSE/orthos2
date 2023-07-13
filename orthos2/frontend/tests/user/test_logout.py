from django.urls import reverse
from django_webtest import WebTest


class Logout(WebTest):

    csrf_checks = True

    fixtures = [
        'orthos2/frontend/tests/fixtures/serverconfigs.json',
        'orthos2/frontend/tests/user/fixtures/users.json'
    ]

    def test_successful_logout(self):
        """Test if a user can log out successfully."""
        # Arrange
        page = self.app.get(reverse('frontend:free_machines'), user='user')

        # Assert user is logged in
        self.assertEqual(page.context['user'].username, 'user')

        # Act
        page = page.click('Logout').maybe_follow()

        # Assert
        self.assertContains(page, 'Login')
