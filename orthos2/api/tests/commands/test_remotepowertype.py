"""Tests for the RemotePowerType Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import RemotePowerType


class RemotePowerTypeCommandTestCase(APITestCase):
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


class AddRemotePowerTypeTest(RemotePowerTypeCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:remotepowertype_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:remotepowertype_add")
        response = self.client.post(
            url,
            {"form": {"name": "AcmeRemotePowerType", "device": "bmc"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not RemotePowerType.objects.filter(name="AcmeRemotePowerType").exists()

    def test_superuser_post_creates_remotepowertype(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype_add")
        response = self.client.post(
            url,
            {"form": {"name": "AcmeRemotePowerType", "device": "bmc"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert RemotePowerType.objects.filter(name="AcmeRemotePowerType").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = RemotePowerType.objects.count()
        url = reverse("api:remotepowertype_add")
        response = self.client.post(url, {"form": {"name": ""}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert RemotePowerType.objects.count() == count_before


class EditRemotePowerTypeTest(RemotePowerTypeCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType"
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:remotepowertype_edit")
        response = self.client.get(url, {"id": self.remotepowertype.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype_edit")
        response = self.client.get(url, {"id": self.remotepowertype.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:remotepowertype_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.remotepowertype.pk,
                    "name": "AcmeRemotePowerType Renamed",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.remotepowertype.refresh_from_db()
        assert self.remotepowertype.name == "AcmeRemotePowerType"

    def test_superuser_post_updates_remotepowertype(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.remotepowertype.pk,
                    "name": "AcmeRemotePowerType Renamed",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.remotepowertype.refresh_from_db()
        assert self.remotepowertype.name == "AcmeRemotePowerType Renamed"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype_edit")
        response = self.client.post(
            url,
            {"form": {"id": 99999, "name": "AcmeRemotePowerType Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteRemotePowerTypeTest(RemotePowerTypeCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType"
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:remotepowertype_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:remotepowertype_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeRemotePowerType"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert RemotePowerType.objects.filter(name="AcmeRemotePowerType").exists()

    def test_superuser_post_deletes_remotepowertype(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeRemotePowerType"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not RemotePowerType.objects.filter(name="AcmeRemotePowerType").exists()

    def test_superuser_post_nonexistent_name_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype_delete")
        response = self.client.post(
            url, {"form": {"name": "Nonexistent"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class RemotePowerTypeInfoTest(RemotePowerTypeCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType"
        )

    def test_get_single_remotepowertype_by_name(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype")
        response = self.client.get(url, {"name": "AcmeRemotePowerType"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmeRemotePowerType"

    def test_get_all_remotepowertypes_when_no_name_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "AcmeRemotePowerType" in [row["name"] for row in data["data"]]

    def test_get_nonexistent_remotepowertype_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:remotepowertype")
        response = self.client.get(url, {"name": "Nonexistent"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:remotepowertype")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:remotepowertype")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
