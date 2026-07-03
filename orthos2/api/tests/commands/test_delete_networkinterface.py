"""Tests for DELETE /api/networkinterface/<id>/."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import NetworkInterface


class DeleteNetworkInterfaceUnauthenticatedTest(APITestCase):
    """Unauthenticated requests must be rejected."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
    ]

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:networkinterface_delete", kwargs={"id": 3})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"


class DeleteNetworkInterfaceTest(APITestCase):
    """Authenticated requests to DELETE /api/networkinterface/<id>/."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
    ]

    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(
            username="superuser", email="super@test.de", password="secret"
        )
        self.regular_user = User.objects.create_user(
            username="user", email="user@test.de", password="secret"
        )
        superuser_token, _ = Token.objects.get_or_create(user=self.superuser)
        self.superuser_token = superuser_token.key
        regular_token, _ = Token.objects.get_or_create(user=self.regular_user)
        self.regular_user_token = regular_token.key

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:networkinterface_delete", kwargs={"id": 3})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()

    def test_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:networkinterface_delete", kwargs={"id": 99999})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "99999" in data["data"]["message"]

    def test_primary_interface_cannot_be_deleted(self) -> None:
        # NetworkInterface pk=1 is primary (machine=1)
        self._auth_superuser()
        url = reverse("api:networkinterface_delete", kwargs={"id": 1})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "primary" in data["data"]["message"].lower()
        assert NetworkInterface.objects.filter(pk=1).exists()

    def test_secondary_interface_is_deleted(self) -> None:
        # NetworkInterface pk=3 is secondary (machine=2, primary=False)
        self._auth_superuser()
        url = reverse("api:networkinterface_delete", kwargs={"id": 3})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not NetworkInterface.objects.filter(pk=3).exists()

    def test_delete_response_contains_deleted_count(self) -> None:
        self._auth_superuser()
        url = reverse("api:networkinterface_delete", kwargs={"id": 3})
        response = self.client.delete(url)
        data = json.loads(response.content)
        theader = data["header"]["theader"]
        assert any(col.get("count") is not None for col in theader)
        total_deleted = sum(row["count"] for row in data["data"])
        assert total_deleted >= 1
