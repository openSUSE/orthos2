"""Tests for the DomainAdmin (domain architecture) Add/Edit/Delete/Info API commands."""

import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from orthos2.data.models import Architecture, Domain, DomainAdmin, ServerConfig


class DomainArchitectureCommandTestCase(APITestCase):
    def setUp(self) -> None:
        self.superuser = User.objects.create_superuser(
            username="superuser", email="super@orthos2.test", password="secret"
        )
        self.regular_user = User.objects.create_user(
            username="user", email="user@orthos2.test", password="secret"
        )
        superuser_token, _ = Token.objects.get_or_create(user=self.superuser)
        self.superuser_token = superuser_token.key
        regular_token, _ = Token.objects.get_or_create(user=self.regular_user)
        self.regular_user_token = regular_token.key

        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        self.domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        self.architecture = Architecture.objects.get(name="x86_64")

    def _auth_superuser(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.superuser_token)

    def _auth_regular(self) -> None:
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.regular_user_token)


class AddDomainArchitectureTest(DomainArchitectureCommandTestCase):
    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:domainarchitecture_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture_add")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:domainarchitecture_add")
        response = self.client.post(
            url,
            {
                "form": {
                    "domain": self.domain.pk,
                    "arch": self.architecture.pk,
                    "contact_email": "support@orthos2.test",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert not DomainAdmin.objects.filter(
            domain=self.domain, arch=self.architecture
        ).exists()

    def test_superuser_post_creates_domainarchitecture(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture_add")
        response = self.client.post(
            url,
            {
                "form": {
                    "domain": self.domain.pk,
                    "arch": self.architecture.pk,
                    "contact_email": "support@orthos2.test",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert DomainAdmin.objects.filter(
            domain=self.domain, arch=self.architecture
        ).exists()

    def test_superuser_post_invalid_data_returns_error(self) -> None:
        self._auth_superuser()
        count_before = DomainAdmin.objects.count()
        url = reverse("api:domainarchitecture_add")
        response = self.client.post(
            url, {"form": {"contact_email": "not-an-email"}}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"
        assert DomainAdmin.objects.count() == count_before


class EditDomainArchitectureTest(DomainArchitectureCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.domainarchitecture = DomainAdmin.objects.create(
            domain=self.domain,
            arch=self.architecture,
            contact_email="support@orthos2.test",
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:domainarchitecture_edit")
        response = self.client.get(url, {"id": self.domainarchitecture.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_get_returns_input_form(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture_edit")
        response = self.client.get(url, {"id": self.domainarchitecture.pk})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INPUT"

    def test_get_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture_edit")
        response = self.client.get(url, {"id": 99999})
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:domainarchitecture_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.domainarchitecture.pk,
                    "domain": self.domain.pk,
                    "arch": self.architecture.pk,
                    "contact_email": "new@orthos2.test",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        self.domainarchitecture.refresh_from_db()
        assert self.domainarchitecture.contact_email == "support@orthos2.test"

    def test_superuser_post_updates_domainarchitecture(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": self.domainarchitecture.pk,
                    "domain": self.domain.pk,
                    "arch": self.architecture.pk,
                    "contact_email": "new@orthos2.test",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        self.domainarchitecture.refresh_from_db()
        assert self.domainarchitecture.contact_email == "new@orthos2.test"

    def test_superuser_post_nonexistent_id_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture_edit")
        response = self.client.post(
            url,
            {
                "form": {
                    "id": 99999,
                    "domain": self.domain.pk,
                    "arch": self.architecture.pk,
                    "contact_email": "new@orthos2.test",
                }
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"


class DeleteDomainArchitectureTest(DomainArchitectureCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.domainarchitecture = DomainAdmin.objects.create(
            domain=self.domain,
            arch=self.architecture,
            contact_email="support@orthos2.test",
        )

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:domainarchitecture_delete")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_post_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:domainarchitecture_delete")
        response = self.client.post(
            url,
            {"form": {"domain": self.domain.name, "arch": self.architecture.name}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
        assert DomainAdmin.objects.filter(pk=self.domainarchitecture.pk).exists()

    def test_superuser_post_deletes_domainarchitecture(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture_delete")
        response = self.client.post(
            url,
            {"form": {"domain": self.domain.name, "arch": self.architecture.name}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert not DomainAdmin.objects.filter(pk=self.domainarchitecture.pk).exists()

    def test_superuser_post_nonexistent_entry_returns_error(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture_delete")
        response = self.client.post(
            url,
            {"form": {"domain": "Nonexistent", "arch": "Nonexistent"}},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert data["data"]["type"] == "ERROR"


class DomainArchitectureInfoTest(DomainArchitectureCommandTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.domainarchitecture = DomainAdmin.objects.create(
            domain=self.domain,
            arch=self.architecture,
            contact_email="support@orthos2.test",
        )

    def test_get_single_entry_by_domain_and_arch(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture")
        response = self.client.get(
            url, {"domain": self.domain.name, "arch": self.architecture.name}
        )
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "INFO"
        assert data["data"]["contact_email"] == "support@orthos2.test"

    def test_get_all_entries_when_no_params_given(self) -> None:
        self._auth_superuser()
        url = reverse("api:domainarchitecture")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "TABLE"
        assert len(data["data"]) == 1

    def test_unauthenticated_returns_auth_required(self) -> None:
        url = reverse("api:domainarchitecture")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "AUTHREQUIRED"

    def test_regular_user_is_rejected(self) -> None:
        self._auth_regular()
        url = reverse("api:domainarchitecture")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = json.loads(response.content)
        assert data["header"]["type"] == "MESSAGE"
        assert "superuser" in data["data"]["message"].lower()
