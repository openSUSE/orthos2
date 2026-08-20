"""Tests for the Architecture Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Architecture


class ArchitectureCommandTestCase(APITestCase):
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


class AddArchitectureTest(ArchitectureCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:architecture_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:architecture_add")
        response = self.client.post(
            url, {"form": {"name": "AcmeArchitecture"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not Architecture.objects.filter(name="AcmeArchitecture").exists()

    def test_superuser_post_creates_architecture(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture_add")
        response = self.client.post(
            url, {"form": {"name": "AcmeArchitecture"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert Architecture.objects.filter(name="AcmeArchitecture").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = Architecture.objects.count()
        url = reverse("api:architecture_add")
        response = self.client.post(url, {"form": {"name": ""}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert Architecture.objects.count() == count_before


class EditArchitectureTest(ArchitectureCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.architecture = Architecture.objects.create(name="AcmeArchitecture")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:architecture_edit")
        response = self.client.get(url, {"id": self.architecture.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture_edit")
        response = self.client.get(url, {"id": self.architecture.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:architecture_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.architecture.pk,
                    "name": "AcmeArchitecture Renamed",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.architecture.refresh_from_db()
        assert self.architecture.name == "AcmeArchitecture"

    def test_superuser_post_updates_architecture(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.architecture.pk,
                    "name": "AcmeArchitecture Renamed",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.architecture.refresh_from_db()
        assert self.architecture.name == "AcmeArchitecture Renamed"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture_edit")
        response = self.client.post(
            url,
            {"form": {"id": 99999, "name": "AcmeArchitecture Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteArchitectureTest(ArchitectureCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.architecture = Architecture.objects.create(name="AcmeArchitecture")

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:architecture_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:architecture_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeArchitecture"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert Architecture.objects.filter(name="AcmeArchitecture").exists()

    def test_superuser_post_deletes_architecture(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture_delete")
        response = self.client.post(
            url, {"form": {"name": "AcmeArchitecture"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not Architecture.objects.filter(name="AcmeArchitecture").exists()

    def test_superuser_post_nonexistent_name_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture_delete")
        response = self.client.post(
            url, {"form": {"name": "Nonexistent"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class DeleteArchitectureProtectionTest(ArchitectureCommandTestCase):
    """Architectures referenced by machines must not be deletable."""

    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    def test_superuser_post_cannot_delete_architecture_with_machines(self) -> None:
        # Architecture pk=1 (x86_64) is referenced by fixture machines.
        architecture = Architecture.objects.get(pk=1)
        self._auth_superuser()
        url = reverse("api:architecture_delete")
        response = self.client.post(
            url, {"form": {"name": architecture.name}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert Architecture.objects.filter(pk=architecture.pk).exists()


class ArchitectureInfoTest(ArchitectureCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.architecture = Architecture.objects.create(name="AcmeArchitecture")

    def test_get_single_architecture_by_name(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture")
        response = self.client.get(url, {"name": "AcmeArchitecture"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmeArchitecture"

    def test_get_all_architectures_when_no_name_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "AcmeArchitecture" in [row["name"] for row in data["data"]]

    def test_get_nonexistent_architecture_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:architecture")
        response = self.client.get(url, {"name": "Nonexistent"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:architecture")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:architecture")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
