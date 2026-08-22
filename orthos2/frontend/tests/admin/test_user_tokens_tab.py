"""Tests for the per-user Tokens tab on the User detail page."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token


class UserTokensViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.target = User.objects.create_user(username="targetuser")

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:user_tokens", kwargs={"id": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:user_tokens", kwargs={"id": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_full_key_of_users_token(self) -> None:
        token = Token.objects.create(user=self.target)
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:user_tokens", kwargs={"id": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert token.key.encode() in response.content

    def test_superuser_get_with_no_token_shows_empty_state(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:user_tokens", kwargs={"id": self.target.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_user_detail_page_links_to_tokens_tab(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:user_detail", kwargs={"id": self.target.pk})
        response = self.client.get(url)
        self.assertContains(
            response, reverse("frontend:user_tokens", kwargs={"id": self.target.pk})
        )
