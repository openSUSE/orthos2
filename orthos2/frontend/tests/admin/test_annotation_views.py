"""Tests for the DeleteAnnotation frontend view."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Annotation, Machine


class DeleteAnnotationViewTest(TestCase):
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def setUp(self) -> None:
        self.machine = Machine.objects.get(pk=1)
        self.annotation = Annotation.objects.create(
            machine=self.machine,
            text="Some note about this machine.",
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:delete_annotation", kwargs={"pk": self.annotation.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_annotation", kwargs={"pk": self.annotation.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_annotation", kwargs={"pk": self.annotation.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_annotation(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_annotation", kwargs={"pk": self.annotation.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Annotation.objects.filter(pk=self.annotation.pk).exists()

    def test_superuser_post_redirects_to_machine_detail(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:delete_annotation", kwargs={"pk": self.annotation.pk})
        response = self.client.post(url)
        assert response.status_code == 302
        expected_url = reverse("frontend:detail", kwargs={"id": self.machine.pk})
        assert response.url == expected_url  # type: ignore[attr-defined]

    def test_regular_user_post_does_not_delete_annotation(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:delete_annotation", kwargs={"pk": self.annotation.pk})
        response = self.client.post(url)
        assert response.status_code == 403
        assert Annotation.objects.filter(pk=self.annotation.pk).exists()
