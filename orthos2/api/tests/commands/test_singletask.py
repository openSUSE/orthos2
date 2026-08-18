"""Tests for the SingleTask Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.taskmanager.models import SingleTask


class SingleTaskCommandTestCase(APITestCase):
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


class AddSingleTaskTest(SingleTaskCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:singletask_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:singletask_add")
        response = self.client.post(
            url,
            {
                "form": {
                    "name": "AcmeTask",
                    "module": "acme.module",
                    "arguments": "[[], {}]",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not SingleTask.objects.filter(name="AcmeTask").exists()

    def test_superuser_post_creates_singletask(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask_add")
        response = self.client.post(
            url,
            {
                "form": {
                    "name": "AcmeTask",
                    "module": "acme.module",
                    "arguments": "[[], {}]",
                    "priority": 10,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert SingleTask.objects.filter(name="AcmeTask").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = SingleTask.objects.count()
        url = reverse("api:singletask_add")
        response = self.client.post(url, {"form": {"name": ""}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert SingleTask.objects.count() == count_before


class EditSingleTaskTest(SingleTaskCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.singletask = SingleTask.objects.create(
            name="AcmeTask", module="acme.module", arguments="[[], {}]"
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:singletask_edit")
        response = self.client.get(url, {"id": self.singletask.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask_edit")
        response = self.client.get(url, {"id": self.singletask.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:singletask_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.singletask.pk,
                    "name": "AcmeTask Renamed",
                    "module": "acme.module",
                    "arguments": "[[], {}]",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.singletask.refresh_from_db()
        assert self.singletask.name == "AcmeTask"

    def test_superuser_post_updates_singletask(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.singletask.pk,
                    "name": "AcmeTask Renamed",
                    "module": "acme.module",
                    "arguments": "[[], {}]",
                    "priority": 10,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.singletask.refresh_from_db()
        assert self.singletask.name == "AcmeTask Renamed"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask_edit")
        response = self.client.post(
            url,
            {"form": {"id": 99999, "name": "AcmeTask Renamed"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteSingleTaskTest(SingleTaskCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.singletask = SingleTask.objects.create(
            name="AcmeTask", module="acme.module", arguments="[[], {}]"
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:singletask_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:singletask_delete")
        response = self.client.post(
            url, {"form": {"id": self.singletask.pk}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert SingleTask.objects.filter(pk=self.singletask.pk).exists()

    def test_superuser_post_deletes_singletask(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask_delete")
        response = self.client.post(
            url, {"form": {"id": self.singletask.pk}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not SingleTask.objects.filter(pk=self.singletask.pk).exists()

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask_delete")
        response = self.client.post(url, {"form": {"id": 99999}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class SingleTaskInfoTest(SingleTaskCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.singletask = SingleTask.objects.create(
            name="AcmeTask", module="acme.module", arguments="[[], {}]"
        )

    def test_get_single_singletask_by_id(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask")
        response = self.client.get(url, {"id": self.singletask.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmeTask"

    def test_get_all_singletasks_when_no_id_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "AcmeTask" in [row["name"] for row in data["data"]]

    def test_get_nonexistent_singletask_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:singletask")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:singletask")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:singletask")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
