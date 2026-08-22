"""Tests for the read-only OIDC diagnostics (Association/Nonce) frontend view."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from social_django.models import Association, Nonce


class OidcDiagnosticsViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.association = Association.objects.create(
            server_url="https://idp.example.test",
            handle="assoc-handle-1",
            secret="",
            issued=0,
            lifetime=0,
            assoc_type="HMAC-SHA1",
        )
        self.nonce = Nonce.objects.create(
            server_url="https://idp.example.test", timestamp=0, salt="nonce-salt-1"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:oidc_diagnostics")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:oidc_diagnostics")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_associations_and_nonces(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:oidc_diagnostics")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"assoc-handle-1" in response.content
        assert b"nonce-salt-1" in response.content

    def test_superuser_get_does_not_expose_association_secret(self) -> None:
        self.association.secret = "super-secret-value"
        self.association.save()
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:oidc_diagnostics")
        response = self.client.get(url)
        assert b"super-secret-value" not in response.content
