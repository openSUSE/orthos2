"""Tests for the Annotation Delete API command."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Annotation, Machine


class DeleteAnnotationTest(APITestCase):
    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

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

        self.machine = Machine.objects.get(pk=1)
        self.annotation = Annotation.objects.create(
            machine=self.machine,
            text="Some note about this machine.",
        )

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:annotation_delete", kwargs={"id": self.annotation.pk})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:annotation_delete", kwargs={"id": self.annotation.pk})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert Annotation.objects.filter(pk=self.annotation.pk).exists()

    def test_superuser_deletes_annotation(self) -> None:
        self._auth_superuser()
        url = reverse("api:annotation_delete", kwargs={"id": self.annotation.pk})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not Annotation.objects.filter(pk=self.annotation.pk).exists()

    def test_superuser_unknown_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:annotation_delete", kwargs={"id": 9999})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
