"""Tests for the Token management frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token


class TokenListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.owner = User.objects.get(username="user")
        self.token = Token.objects.create(user=self.owner)

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:tokens")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(self.owner)
        url = reverse("frontend:tokens")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_tokens(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:tokens")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"user" in response.content

    def test_superuser_get_shows_full_key(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:tokens")
        response = self.client.get(url)
        assert self.token.key.encode() in response.content

    def test_revoke_link_does_not_embed_key_in_url(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:tokens")
        response = self.client.get(url)
        delete_url = reverse("frontend:delete_token", kwargs={"user_id": self.owner.pk})
        assert delete_url.encode() in response.content
        assert self.token.key not in delete_url


class DeleteTokenViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.owner = User.objects.get(username="user")
        self.token = Token.objects.create(user=self.owner)

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_token", kwargs={"user_id": self.owner.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(self.owner)
        url = reverse("frontend:delete_token", kwargs={"user_id": self.owner.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_token", kwargs={"user_id": self.owner.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_revokes_token(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_token", kwargs={"user_id": self.owner.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Token.objects.filter(pk=self.token.key).exists()

    def test_regular_user_post_does_not_revoke_token(self) -> None:
        self.client.force_login(self.owner)
        url = reverse("frontend:delete_token", kwargs={"user_id": self.owner.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert Token.objects.filter(pk=self.token.key).exists()
