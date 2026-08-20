"""Tests for the DailyTask CRUD frontend views and the Execute/Switch actions."""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from orthos2.taskmanager.models import DailyTask


class DailyTaskListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        DailyTask.objects.create(
            name="AcmeDailyTask", module="acme.module", arguments="[[], {}]"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:dailytasks")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:dailytasks")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_dailytasks(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:dailytasks")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeDailyTask" in response.content


class DailyTaskDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask", module="acme.module", arguments="[[], {}]"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:dailytask_detail", kwargs={"id": self.dailytask.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:dailytask_detail", kwargs={"id": self.dailytask.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:dailytask_detail", kwargs={"id": self.dailytask.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeDailyTask" in response.content

    def test_nonexistent_dailytask_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:dailytask_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewDailyTaskViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_dailytask")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_dailytask")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_dailytask")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_dailytask(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_dailytask")
        response = self.client.post(
            url,
            {
                "task": "orthos2.taskmanager.tasks.daily.DailyCheckForPrimaryNetwork",
                "arguments": "[[], {}]",
                "priority": 10,
                "enabled": True,
            },
        )
        assert response.status_code == 302
        assert DailyTask.objects.filter(
            name="DailyCheckForPrimaryNetwork",
            module="orthos2.taskmanager.tasks.daily",
        ).exists()

    def test_regular_user_post_does_not_create_dailytask(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_dailytask")
        response = self.client.post(
            url,
            {
                "task": "orthos2.taskmanager.tasks.daily.DailyCheckForPrimaryNetwork",
                "arguments": "[[], {}]",
                "priority": 10,
                "enabled": True,
            },
        )
        assert response.status_code == 403
        assert not DailyTask.objects.filter(name="DailyCheckForPrimaryNetwork").exists()


class DailyTaskDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask", module="acme.module", arguments="[[], {}]"
        )

    def test_superuser_post_updates_dailytask(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_dailytask", kwargs={"pk": self.dailytask.pk})
        response = self.client.post(
            url,
            {
                "task": "orthos2.taskmanager.tasks.daily.DailyMachineChecks",
                "arguments": "[[], {}]",
                "priority": 10,
                "enabled": True,
            },
        )
        assert response.status_code == 302
        self.dailytask.refresh_from_db()
        assert self.dailytask.name == "DailyMachineChecks"
        assert self.dailytask.module == "orthos2.taskmanager.tasks.daily"

    def test_regular_user_post_does_not_update_dailytask(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_dailytask", kwargs={"pk": self.dailytask.pk})
        response = self.client.post(
            url,
            {
                "task": "orthos2.taskmanager.tasks.daily.DailyMachineChecks",
                "arguments": "[[], {}]",
                "priority": 10,
                "enabled": True,
            },
        )
        assert response.status_code == 403
        self.dailytask.refresh_from_db()
        assert self.dailytask.name == "AcmeDailyTask"


class DeleteDailyTaskViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask", module="acme.module", arguments="[[], {}]"
        )

    def test_superuser_post_deletes_dailytask(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_dailytask", kwargs={"pk": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not DailyTask.objects.filter(pk=self.dailytask.pk).exists()

    def test_regular_user_post_does_not_delete_dailytask(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_dailytask", kwargs={"pk": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert DailyTask.objects.filter(pk=self.dailytask.pk).exists()


class DailyTaskExecuteViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask",
            module="acme.module",
            arguments="[[], {}]",
            enabled=True,
        )

    def test_unauthenticated_post_redirects_to_login(self) -> None:
        url = reverse("frontend:dailytask_execute", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_post_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:dailytask_execute", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == 403

    def test_get_is_not_allowed(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:dailytask_execute", kwargs={"id": self.dailytask.pk})
        response = self.client.get(url)
        assert response.status_code == 405

    def test_superuser_post_backdates_executed_at_and_redirects(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:dailytask_execute", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        self.dailytask.refresh_from_db()
        assert self.dailytask.executed_at < timezone.now() - timedelta(hours=23)


class DailyTaskSwitchViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.dailytask = DailyTask.objects.create(
            name="AcmeDailyTask",
            module="acme.module",
            arguments="[[], {}]",
            enabled=True,
        )

    def test_regular_user_post_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:dailytask_switch", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url, {"action": "disable"})
        assert response.status_code == 403

    def test_superuser_post_disables_task(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:dailytask_switch", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url, {"action": "disable"})
        assert response.status_code == 302
        self.dailytask.refresh_from_db()
        assert self.dailytask.enabled is False

    def test_superuser_post_enables_task(self) -> None:
        self.dailytask.enabled = False
        self.dailytask.save()
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:dailytask_switch", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url, {"action": "enable"})
        assert response.status_code == 302
        self.dailytask.refresh_from_db()
        assert self.dailytask.enabled is True

    def test_unknown_action_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:dailytask_switch", kwargs={"id": self.dailytask.pk})
        response = self.client.post(url, {"action": "frobnicate"})
        assert response.status_code == 404
