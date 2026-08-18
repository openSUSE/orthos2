"""Tests for the Domain Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Domain, ServerConfig


class DomainCommandTestCase(APITestCase):
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

        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)

    def _payload(self, **overrides) -> dict:
        payload = {
            "name": "orthos2.test",
            "cobbler_server_username": "cobbler",
            "cobbler_server_password": "cobbler",
            "ip_v4": "127.0.0.1",
            "ip_v6": "::1",
            "subnet_mask_v4": 24,
            "subnet_mask_v6": 64,
            "enable_v4": True,
            "enable_v6": True,
            "dynamic_range_v4_start": "127.0.0.1",
            "dynamic_range_v4_end": "127.0.0.1",
            "dynamic_range_v6_start": "::1",
            "dynamic_range_v6_end": "::1",
        }
        payload.update(overrides)
        return payload


class AddDomainTest(DomainCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:domain_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:domain_add")
        response = self.client.post(url, {"form": self._payload()}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not Domain.objects.filter(name="orthos2.test").exists()

    def test_superuser_post_creates_domain(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain_add")
        response = self.client.post(url, {"form": self._payload()}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert Domain.objects.filter(name="orthos2.test").exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = Domain.objects.count()
        url = reverse("api:domain_add")
        response = self.client.post(url, {"form": {"name": ""}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert Domain.objects.count() == count_before


class EditDomainTest(DomainCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:domain_edit")
        response = self.client.get(url, {"id": self.domain.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain_edit")
        response = self.client.get(url, {"id": self.domain.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:domain_edit")
        response = self.client.post(
            url,
            {"form": self._payload(id=self.domain.pk, cobbler_server_username="new")},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.domain.refresh_from_db()
        assert self.domain.cobbler_server_username != "new"

    def test_superuser_post_updates_domain(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain_edit")
        response = self.client.post(
            url,
            {"form": self._payload(id=self.domain.pk, cobbler_server_username="new")},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.domain.refresh_from_db()
        assert self.domain.cobbler_server_username == "new"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain_edit")
        response = self.client.post(
            url,
            {"form": self._payload(id=99999)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteDomainTest(DomainCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:domain_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:domain_delete")
        response = self.client.post(
            url, {"form": {"name": "orthos2.test"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert Domain.objects.filter(name="orthos2.test").exists()

    def test_superuser_post_deletes_domain(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain_delete")
        response = self.client.post(
            url, {"form": {"name": "orthos2.test"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not Domain.objects.filter(name="orthos2.test").exists()

    def test_superuser_post_nonexistent_name_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain_delete")
        response = self.client.post(
            url, {"form": {"name": "Nonexistent"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class DeleteDomainProtectionTest(DomainCommandTestCase):
    """Domains referenced by machines must not be deletable."""

    fixtures = ["orthos2/data/fixtures/tests/test_machines.json"]

    def test_superuser_post_cannot_delete_domain_with_machines(self) -> None:
        domain = Domain.objects.get(pk=1)
        self._auth_superuser()
        url = reverse("api:domain_delete")
        response = self.client.post(url, {"form": {"name": domain.name}}, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert Domain.objects.filter(pk=domain.pk).exists()


class DomainInfoTest(DomainCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )

    def test_get_single_domain_by_name(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain")
        response = self.client.get(url, {"name": "orthos2.test"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["name"] == "orthos2.test"

    def test_get_all_domains_when_no_name_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert "orthos2.test" in [row["name"] for row in data["data"]]

    def test_get_nonexistent_domain_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:domain")
        response = self.client.get(url, {"name": "Nonexistent"})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:domain")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:domain")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
