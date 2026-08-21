"""Tests for the Machine Edit API command."""

import json
from unittest import mock

from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Architecture, Machine, ServerConfig, System
from orthos2.data.models.domain import Domain
from orthos2.frontend.views.machine import MACHINE_FIELDS


class EditMachineCommandTestCase(APITestCase):
    fixtures = [
        "orthos2/data/fixtures/systems.json",
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

    def _valid_form_data(self, **overrides: object) -> dict:
        data = model_to_dict(self.machine, fields=MACHINE_FIELDS)
        data = {key: ("" if value is None else value) for key, value in data.items()}
        data.update(overrides)
        return data


class EditMachineTest(EditMachineCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:machine_edit_get")
        response = self.client.get(url, {"fqdn": self.machine.fqdn})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:machine_edit_get")
        response = self.client.get(url, {"fqdn": self.machine.fqdn})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:machine_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {"form": self._valid_form_data(comment="updated")},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.machine.refresh_from_db()
        assert self.machine.comment != "updated"

    def test_superuser_post_updates_machine(self) -> None:
        self._auth_superuser()
        url = reverse("api:machine_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {"form": self._valid_form_data(comment="updated")},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.machine.refresh_from_db()
        assert self.machine.comment == "updated"

    def test_superuser_post_hypervisor_on_non_virtual_system_returns_error(
        self,
    ) -> None:
        self._auth_superuser()
        url = reverse("api:machine_edit_post", kwargs={"fqdn": self.machine.fqdn})
        response = self.client.post(
            url,
            {"form": self._valid_form_data(hypervisor=self.machine.pk)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        self.machine.refresh_from_db()
        assert self.machine.hypervisor_id is None

    def test_superuser_post_unknown_fqdn_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse(
            "api:machine_edit_post", kwargs={"fqdn": "does-not-exist.foo.bar.de"}
        )
        response = self.client.post(
            url,
            {"form": self._valid_form_data()},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
