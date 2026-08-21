"""Tests for the MachineDetailedEdit frontend view."""

from unittest import mock

from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import Architecture, Machine, ServerConfig, System
from orthos2.data.models.domain import Domain
from orthos2.frontend.views.machine import MACHINE_FIELDS


class MachineDetailedEditViewTest(TestCase):
    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
        "orthos2/data/fixtures/architectures.json",
    ]

    @mock.patch("orthos2.data.models.machine.is_dns_resolvable")
    def setUp(self, m_is_dns_resolvable: mock.MagicMock) -> None:
        m_is_dns_resolvable.return_value = True

        ServerConfig.objects.create(key="domain.validendings", value="bar.de")

        Domain(
            name="foo.bar.de",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        ).save()

        self.machine = Machine()
        self.machine.pk = 1
        self.machine.system = System.get_system_manager().get_by_natural_key(
            "BareMetal"
        )
        self.machine.fqdn = "machine1.foo.bar.de"
        self.machine.architecture_id = (
            Architecture.get_architecture_manager().get_by_natural_key("x86_64").id
        )
        self.machine.save()

    def _valid_post_data(self, **overrides: object) -> dict:
        data = model_to_dict(self.machine, fields=MACHINE_FIELDS)
        data = {key: ("" if value is None else value) for key, value in data.items()}
        data.update(overrides)
        return data

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:edit_machine", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_machine", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_machine", kwargs={"pk": self.machine.pk})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_machine(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_machine", kwargs={"pk": self.machine.pk})
        response = self.client.post(url, self._valid_post_data(comment="updated"))
        assert response.status_code == 302
        self.machine.refresh_from_db()
        assert self.machine.comment == "updated"

    def test_regular_user_post_does_not_update_machine(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:edit_machine", kwargs={"pk": self.machine.pk})
        response = self.client.post(url, self._valid_post_data(comment="updated"))
        assert response.status_code == 403
        self.machine.refresh_from_db()
        assert self.machine.comment != "updated"

    def test_superuser_post_hypervisor_on_non_virtual_system_shows_error(
        self,
    ) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_machine", kwargs={"pk": self.machine.pk})
        response = self.client.post(
            url, self._valid_post_data(hypervisor=self.machine.pk)
        )
        assert response.status_code == 200
        self.machine.refresh_from_db()
        assert self.machine.hypervisor_id is None

    def test_superuser_post_collect_system_information_without_full_connectivity_shows_error(
        self,
    ) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:edit_machine", kwargs={"pk": self.machine.pk})
        response = self.client.post(
            url,
            self._valid_post_data(
                collect_system_information=True,
                check_connectivity=Machine.Connectivity.PING,
            ),
        )
        assert response.status_code == 200
        self.machine.refresh_from_db()
        assert self.machine.check_connectivity != Machine.Connectivity.PING
