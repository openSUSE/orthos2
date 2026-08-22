"""Tests for the SingleTask CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.taskmanager.models import SingleTask


class SingleTaskListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        SingleTask.objects.create(
            name="AcmeTask", module="acme.module", arguments="[[], {}]"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:singletasks")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:singletasks")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_singletasks(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:singletasks")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeTask" in response.content


class SingleTaskDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.singletask = SingleTask.objects.create(
            name="AcmeTask", module="acme.module", arguments="[[], {}]"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:singletask_detail", kwargs={"id": self.singletask.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:singletask_detail", kwargs={"id": self.singletask.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:singletask_detail", kwargs={"id": self.singletask.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeTask" in response.content

    def test_nonexistent_singletask_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:singletask_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class NewSingleTaskViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_singletask")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_singletask")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_singletask")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_singletask(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_singletask")
        response = self.client.post(
            url,
            {
                "task": "orthos2.taskmanager.tasks.netbox.NetboxFetchMachine",
                "arguments": "[[], {}]",
                "priority": 10,
            },
        )
        assert response.status_code == 302
        assert SingleTask.objects.filter(
            name="NetboxFetchMachine", module="orthos2.taskmanager.tasks.netbox"
        ).exists()

    def test_regular_user_post_does_not_create_singletask(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_singletask")
        response = self.client.post(
            url,
            {
                "task": "orthos2.taskmanager.tasks.netbox.NetboxFetchMachine",
                "arguments": "[[], {}]",
            },
        )
        assert response.status_code == 403
        assert not SingleTask.objects.filter(name="NetboxFetchMachine").exists()


class SingleTaskDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.singletask = SingleTask.objects.create(
            name="AcmeTask", module="acme.module", arguments="[[], {}]"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_singletask(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.post(
            url,
            {
                "task": "orthos2.taskmanager.tasks.netbox.NetboxFetchBMC",
                "arguments": "[[], {}]",
                "priority": 10,
            },
        )
        assert response.status_code == 302
        self.singletask.refresh_from_db()
        assert self.singletask.name == "NetboxFetchBMC"
        assert self.singletask.module == "orthos2.taskmanager.tasks.netbox"

    def test_regular_user_post_does_not_update_singletask(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.post(
            url,
            {
                "task": "orthos2.taskmanager.tasks.netbox.NetboxFetchBMC",
                "arguments": "[[], {}]",
            },
        )
        assert response.status_code == 403
        self.singletask.refresh_from_db()
        assert self.singletask.name == "AcmeTask"


class DeleteSingleTaskViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.singletask = SingleTask.objects.create(
            name="AcmeTask", module="acme.module", arguments="[[], {}]"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_singletask(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not SingleTask.objects.filter(pk=self.singletask.pk).exists()

    def test_regular_user_post_does_not_delete_singletask(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_singletask", kwargs={"pk": self.singletask.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert SingleTask.objects.filter(pk=self.singletask.pk).exists()


class SingleTaskToggleRunningViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.singletask = SingleTask.objects.create(
            name="AcmeTask", module="acme.module", arguments="[[], {}]", running=True
        )

    def test_unauthenticated_post_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:singletask_toggle_running", kwargs={"id": self.singletask.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_post_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:singletask_toggle_running", kwargs={"id": self.singletask.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 403

    def test_get_is_not_allowed(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:singletask_toggle_running", kwargs={"id": self.singletask.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 405

    def test_superuser_post_flips_running_from_true_to_false(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:singletask_toggle_running", kwargs={"id": self.singletask.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        self.singletask.refresh_from_db()
        assert self.singletask.running is False

    def test_superuser_post_flips_running_from_false_to_true(self) -> None:
        self.singletask.running = False
        self.singletask.save()
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:singletask_toggle_running", kwargs={"id": self.singletask.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        self.singletask.refresh_from_db()
        assert self.singletask.running is True
