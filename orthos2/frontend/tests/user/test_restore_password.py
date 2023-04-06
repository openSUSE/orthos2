from django.contrib.auth.models import User
from django.urls import reverse
from django_webtest import WebTest

from orthos2.taskmanager.models import SingleTask


class CreateAccount(WebTest):

    csrf_checks = True

    fixtures = [
        'frontend/tests/fixtures/serverconfigs.json',
        'frontend/tests/user/fixtures/users.json'
    ]

    def test_successful_restore_password(self):
        """Test restore password functionality."""
        form = self.app.get(reverse('frontend:password_restore')).form
        form['login'] = 'user'
        form['email'] = 'user@foo.bar'
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context['user'].username, 'user')
        self.assertIn(reverse('frontend:login'), page.request.url)
        self.assertContains(page, 'Password restored - check your mails')

        # check for tasks
        self.assertEqual(SingleTask.objects.all().count(), 2)

        task_send_restored_password = SingleTask.objects.first()
        task_check_multiple_accounts = SingleTask.objects.last()

        user = User.objects.get(username='user')

        self.assertEqual(task_send_restored_password.name, 'SendRestoredPassword')
        self.assertIn(str(user.pk), task_send_restored_password.arguments)
        self.assertEqual(task_check_multiple_accounts.name, 'CheckMultipleAccounts')
        self.assertIn(str(user.pk), task_check_multiple_accounts.arguments)

    def test_unknown_login(self):
        """Check if login exists."""
        form = self.app.get(reverse('frontend:password_restore')).form
        form['login'] = 'unknown'
        form['email'] = 'user@foo.bar'
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context['user'].username, 'unknown')
        self.assertIn(reverse('frontend:password_restore'), page.request.url)
        self.assertContains(page, 'E-Mail/login does not exist')

    def test_unknown_email(self):
        """Check if email address exists."""
        form = self.app.get(reverse('frontend:password_restore')).form
        form['login'] = 'user'
        form['email'] = 'unknown@unknown.foo'
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context['user'].username, 'user')
        self.assertIn(reverse('frontend:password_restore'), page.request.url)
        self.assertContains(page, 'E-Mail/login does not exist')

    def test_invalid_email(self):
        """Check for valid email address."""
        form = self.app.get(reverse('frontend:password_restore')).form
        form['login'] = 'user'
        form['email'] = 'user@invalid'
        page = form.submit().maybe_follow()

        self.assertNotEqual(page.context['user'].username, 'user')
        self.assertIn(reverse('frontend:password_restore'), page.request.url)
        self.assertContains(page, 'Enter a valid email address')
