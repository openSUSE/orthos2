"""Tests for the DailyTask Add/Edit/Delete/Info API commands and the Execute/Switch actions."""

import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.taskmanager.models import DailyTask


class DailyTaskCommandTestCase(APITestCase):
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


class AddDailyTaskTest(DailyTaskCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:dailytask_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_superuser_post_creates_dailytask(self) -> None:
        self._auth_superuser()
        url = reverse("api:dailytask_add")
        response = self.client.post(
            url,
            {
                "form": {
                    "name": "AcmeDailyTask",
                    "module": "acme.module",
                    "arguments": "[[], {}]",
                    "priority": 10,
                    "enabled": True,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert DailyTask.objects.filter(name="AcmeDailyTask").exists()

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:dailytask_add")
        response = self.client.post(
            url,
            {
                "form": {
                    "name": "AcmeDailyTask",
                    "module": "acme.module",
                    "arguments": "[[], {}]",
                    "priority": 10,
                    "enabled": True,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert "superuser" in data["data"]["message"].lower()
        assert not DailyTask.objects.filter(name="AcmeDailyTask").exists()


class EditDailyTaskTest(DailyTaskCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask", module="acme.module", arguments="[[], {}]"
        )

    def test_superuser_post_updates_dailytask(self) -> None:
        self._auth_superuser()
        url = reverse("api:dailytask_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.dailytask.pk,
                    "name": "AcmeDailyTask Renamed",
                    "module": "acme.module",
                    "arguments": "[[], {}]",
                    "priority": 10,
                    "enabled": True,
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.dailytask.refresh_from_db()
        assert self.dailytask.name == "AcmeDailyTask Renamed"


class DeleteDailyTaskTest(DailyTaskCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask", module="acme.module", arguments="[[], {}]"
        )

    def test_superuser_post_deletes_dailytask(self) -> None:
        self._auth_superuser()
        url = reverse("api:dailytask_delete")
        response = self.client.post(
            url, {"form": {"id": self.dailytask.pk}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not DailyTask.objects.filter(pk=self.dailytask.pk).exists()

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:dailytask_delete")
        response = self.client.post(
            url, {"form": {"id": self.dailytask.pk}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert DailyTask.objects.filter(pk=self.dailytask.pk).exists()


class DailyTaskInfoTest(DailyTaskCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask", module="acme.module", arguments="[[], {}]"
        )

    def test_get_single_dailytask_by_id(self) -> None:
        self._auth_superuser()
        url = reverse("api:dailytask")
        response = self.client.get(url, {"id": self.dailytask.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "AcmeDailyTask"

    def test_get_all_dailytasks_when_no_id_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:dailytask")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "AcmeDailyTask" in [row["name"] for row in data["data"]]

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:dailytask")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"


class ExecuteDailyTaskCommandTest(DailyTaskCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask",
            module="acme.module",
            arguments="[[], {}]",
            enabled=True,
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:dailytask_execute", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:dailytask_execute", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert "superuser" in data["data"]["message"].lower()

    def test_superuser_post_backdates_executed_at(self) -> None:
        self._auth_superuser()
        url = reverse("api:dailytask_execute", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        self.dailytask.refresh_from_db()
        assert self.dailytask.executed_at < timezone.now() - timedelta(hours=23)

    def test_disabled_task_returns_error(self) -> None:
        self.dailytask.enabled = False
        self.dailytask.save()
        self._auth_superuser()
        url = reverse("api:dailytask_execute", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["data"]["type"] == "ERROR"

    def test_already_running_task_returns_error(self) -> None:
        self.dailytask.running = True
        self.dailytask.save()
        self._auth_superuser()
        url = reverse("api:dailytask_execute", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["data"]["type"] == "ERROR"


class SwitchDailyTaskCommandTest(DailyTaskCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask",
            module="acme.module",
            arguments="[[], {}]",
            enabled=True,
        )

    def test_superuser_post_disables_task(self) -> None:
        self._auth_superuser()
        url = reverse("api:dailytask_switch", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url, {"action": "disable"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        self.dailytask.refresh_from_db()
        assert self.dailytask.enabled is False

    def test_superuser_post_enables_task(self) -> None:
        self.dailytask.enabled = False
        self.dailytask.save()
        self._auth_superuser()
        url = reverse("api:dailytask_switch", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url, {"action": "enable"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        self.dailytask.refresh_from_db()
        assert self.dailytask.enabled is True

    def test_unknown_action_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:dailytask_switch", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url, {"action": "frobnicate"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["data"]["type"] == "ERROR"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:dailytask_switch", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url, {"action": "disable"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert "superuser" in data["data"]["message"].lower()
