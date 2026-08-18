"""Tests for the Platform Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Manufacturer, Platform


class PlatformCommandTestCase(APITestCase):
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
        self.manufacturer = Manufacturer.objects.create(name="AcmeCorp")

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class AddPlatformTest(PlatformCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:platform_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:platform_add")
        response = self.client.post(
            url,
            {"form": {"name": "AcmePlatform", "manufacturer": self.manufacturer.pk}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not Platform.objects.filter(name="AcmePlatform").exists()

    def test_superuser_post_creates_platform(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform_add")
        response = self.client.post(
            url,
            {"form": {"name": "AcmePlatform", "manufacturer": self.manufacturer.pk}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert Platform.objects.filter(name="AcmePlatform").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = Platform.objects.count()
        url = reverse("api:platform_add")
        response = self.client.post(
            url,
            {"form": {"name": "", "manufacturer": self.manufacturer.pk}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert Platform.objects.count() == count_before


class EditPlatformTest(PlatformCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.platform = Platform.objects.create(
            name="AcmePlatform", manufacturer=self.manufacturer
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:platform_edit")
        response = self.client.get(url, {"id": self.platform.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform_edit")
        response = self.client.get(url, {"id": self.platform.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:platform_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.platform.pk,
                    "name": "AcmePlatform Renamed",
                    "manufacturer": self.manufacturer.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.platform.refresh_from_db()
        assert self.platform.name == "AcmePlatform"

    def test_superuser_post_updates_platform(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.platform.pk,
                    "name": "AcmePlatform Renamed",
                    "manufacturer": self.manufacturer.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.platform.refresh_from_db()
        assert self.platform.name == "AcmePlatform Renamed"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": 99999,
                    "name": "AcmePlatform Renamed",
                    "manufacturer": self.manufacturer.pk,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeletePlatformTest(PlatformCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.platform = Platform.objects.create(
            name="AcmePlatform", manufacturer=self.manufacturer
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:platform_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:platform_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmePlatform"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert Platform.objects.filter(name="AcmePlatform").exists()

    def test_superuser_post_deletes_platform(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmePlatform"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not Platform.objects.filter(name="AcmePlatform").exists()

    def test_superuser_post_nonexistent_name_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform_delete")
        response = self.client.post(
            url, {"form": {"name": "Nonexistent"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class PlatformInfoTest(PlatformCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.platform = Platform.objects.create(
            name="AcmePlatform", manufacturer=self.manufacturer
        )

    def test_get_single_platform_by_name(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform")
        response = self.client.get(url, {"name": "AcmePlatform"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmePlatform"

    def test_get_all_platforms_when_no_name_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "AcmePlatform" in [row["name"] for row in data["data"]]

    def test_get_nonexistent_platform_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:platform")
        response = self.client.get(url, {"name": "Nonexistent"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:platform")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:platform")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
