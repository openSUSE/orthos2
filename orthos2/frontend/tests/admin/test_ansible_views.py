from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django_webtest import WebTest  # type: ignore

from orthos2.data.models import AnsibleScanResult, Machine


class AnsibleResultListViewTest(WebTest):
    """Tests for AnsibleResultListView."""

    csrf_checks = True
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_list_view_requires_superuser(self) -> None:
        """Should require superuser access."""
        # Act
        # Try to access as regular user
        response = self.app.get(
            reverse("frontend:ansible_results_list"), user="user", expect_errors=True
        )

        # Assert
        # Should be redirected or forbidden
        assert response.status_code in [302, 403]

    def test_list_view_accessible_to_superuser(self) -> None:
        """Should be accessible to superuser."""
        # Arrange
        machine = Machine.objects.first()
        AnsibleScanResult.objects.create(
            machine=machine, facts_raw={}, ansible_version="2.9.27"
        )

        # Act
        response = self.app.get(
            reverse("frontend:ansible_results_list"), user="superuser"
        )

        # Assert
        assert response.status_code == 200
        assert "Ansible Scan Results" in response.text

    def test_list_view_filter_by_machine_id(self) -> None:
        """Should filter results by machine_id."""
        # Arrange
        machine1 = Machine.objects.get(fqdn="testsys.orthos2.test")
        machine2 = Machine.objects.get(fqdn="cobbler.orthos2.test")

        AnsibleScanResult.objects.create(
            machine=machine1, facts_raw={}, ansible_version="2.9.27"
        )
        AnsibleScanResult.objects.create(
            machine=machine2, facts_raw={}, ansible_version="2.9.27"
        )

        # Act
        response = self.app.get(
            reverse("frontend:ansible_results_list") + f"?machine_id={machine1.pk}",
            user="superuser",
        )

        # Assert
        # Should show machine1's result but not machine2's
        assert machine1.fqdn in response.text
        assert machine2.fqdn not in response.text or response.text.count(
            machine2.fqdn
        ) < response.text.count(machine1.fqdn)

    def test_list_view_filter_by_date_range(self) -> None:
        """Should filter results by date range."""
        # Arrange
        machine = Machine.objects.first()
        old_date = timezone.now() - timedelta(days=10)
        new_date = timezone.now()

        AnsibleScanResult.objects.create(
            machine=machine,
            facts_raw={},
            ansible_version="2.9.27",
            run_date=old_date,
        )
        AnsibleScanResult.objects.create(
            machine=machine,
            facts_raw={},
            ansible_version="2.9.27",
            run_date=new_date,
        )

        # Filter to only recent results
        date_from = (timezone.now() - timedelta(days=5)).strftime("%Y-%m-%d")

        # Act
        response = self.app.get(
            reverse("frontend:ansible_results_list") + f"?date_from={date_from}",
            user="superuser",
        )

        # Assert
        # Should have results (the new one)
        assert response.status_code == 200

    def test_list_view_search_by_fqdn(self) -> None:
        """Should search results by machine FQDN."""
        # Arrange
        machine1 = Machine.objects.get(fqdn="testsys.orthos2.test")
        machine2 = Machine.objects.get(fqdn="cobbler.orthos2.test")

        AnsibleScanResult.objects.create(
            machine=machine1, facts_raw={}, ansible_version="2.9.27"
        )
        AnsibleScanResult.objects.create(
            machine=machine2, facts_raw={}, ansible_version="2.9.27"
        )

        # Act
        response = self.app.get(
            reverse("frontend:ansible_results_list") + "?search=testsys",
            user="superuser",
        )

        # Assert
        # Should find testsys
        assert "testsys" in response.text

    def test_list_view_pagination(self) -> None:
        """Should paginate results (50 per page)."""
        # Arrange
        machine = Machine.objects.first()

        # Create 60 results
        for _ in range(60):
            AnsibleScanResult.objects.create(
                machine=machine, facts_raw={}, ansible_version="2.9.27"
            )

        # Act
        response = self.app.get(
            reverse("frontend:ansible_results_list"), user="superuser"
        )

        # Assert
        # Should show pagination controls
        assert response.status_code == 200
        # Should have results on page
        results = response.context["results"]
        assert len(results) == 50  # paginate_by=50


class AnsibleResultDetailViewTest(WebTest):
    """Tests for ansible_result_detail view."""

    csrf_checks = True
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_detail_view_requires_superuser(self) -> None:
        """Should require superuser access."""
        # Arrange
        machine = Machine.objects.first()
        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw={}, ansible_version="2.9.27"
        )

        # Act
        response = self.app.get(
            reverse("frontend:ansible_result_detail", args=[result.pk]),
            user="user",
            expect_errors=True,
        )

        # Assert
        assert response.status_code in [302, 403]

    def test_detail_view_shows_result(self) -> None:
        """Should show ansible scan result details."""
        # Arrange
        machine = Machine.objects.first()
        facts = {"ansible_processor_count": 2, "ansible_memtotal_mb": 16384}
        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw=facts, ansible_version="2.9.27"
        )

        # Act
        response = self.app.get(
            reverse("frontend:ansible_result_detail", args=[result.pk]),
            user="superuser",
        )

        # Assert
        assert response.status_code == 200
        assert "2.9.27" in response.text

    def test_detail_view_nonexistent_result(self) -> None:
        """Should return 404 for nonexistent result."""
        # Act
        response = self.app.get(
            reverse("frontend:ansible_result_detail", args=[99999]),
            user="superuser",
            expect_errors=True,
        )

        # Assert
        assert response.status_code == 404


class AnsibleResultDeleteViewTest(TestCase):
    """Tests for ansible_result_delete view."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_delete_requires_superuser(self) -> None:
        """Should require superuser access."""
        # Arrange
        machine = Machine.objects.first()
        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw={}, ansible_version="2.9.27"
        )

        user = User.objects.get(username="user")
        self.client.force_login(user)

        # Act
        response = self.client.post(
            reverse("frontend:ansible_result_delete", args=[result.pk])
        )

        # Assert
        assert response.status_code in [302, 403]

    def test_delete_removes_result(self) -> None:
        """Should delete result from database."""
        # Arrange
        machine = Machine.objects.first()
        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw={}, ansible_version="2.9.27"
        )
        result_pk = result.pk

        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)

        # Act
        response = self.client.post(
            reverse("frontend:ansible_result_delete", args=[result_pk])
        )

        # Assert
        assert response.status_code == 302  # Redirect
        assert not AnsibleScanResult.objects.filter(pk=result_pk).exists()

    def test_delete_redirects_to_list(self) -> None:
        """Should redirect to list when redirect_to=list."""
        # Arrange
        machine = Machine.objects.first()
        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw={}, ansible_version="2.9.27"
        )

        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)

        # Act
        response = self.client.post(
            reverse("frontend:ansible_result_delete", args=[result.pk]),
            {"redirect_to": "list"},
        )

        # Assert
        assert response.status_code == 302
        assert response.url == reverse("frontend:ansible_results_list")  # type: ignore


class AnsibleResultBulkDeleteViewTest(TestCase):
    """Tests for ansible_result_bulk_delete view."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_bulk_delete_removes_multiple(self) -> None:
        """Should delete multiple results."""
        # Arrange
        machine = Machine.objects.first()

        results = []
        for _ in range(5):
            result = AnsibleScanResult.objects.create(
                machine=machine, facts_raw={}, ansible_version="2.9.27"
            )
            results.append(result)

        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)

        # Delete first 3
        result_ids = [results[0].pk, results[1].pk, results[2].pk]

        # Act
        response = self.client.post(
            reverse("frontend:ansible_results_bulk_delete"),
            {"result_ids": result_ids},
        )

        # Assert
        assert response.status_code == 302
        assert AnsibleScanResult.objects.count() == 2  # 2 remaining

    def test_bulk_delete_empty_selection(self) -> None:
        """Should show warning when no results selected."""
        # Arrange
        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)

        # Act
        response = self.client.post(
            reverse("frontend:ansible_results_bulk_delete"),
            {"result_ids": []},
        )

        # Assert
        assert response.status_code == 302


class AnsibleResultApplyViewTest(TestCase):
    """Tests for ansible_result_apply view."""

    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    @mock.patch("orthos2.data.models.AnsibleScanResult.apply_to_machine")
    def test_apply_calls_apply_to_machine(self, mocked_apply: mock.MagicMock) -> None:
        """Should call apply_to_machine method."""
        # Arrange
        machine = Machine.objects.first()
        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw={}, ansible_version="2.9.27"
        )

        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)

        # Act
        response = self.client.post(
            reverse("frontend:ansible_result_apply", args=[result.pk])
        )

        # Assert
        assert response.status_code == 302
        mocked_apply.assert_called_once()

    def test_apply_without_machine(self) -> None:
        """Should show error when result has no machine."""
        # Arrange
        result = AnsibleScanResult.objects.create(
            machine=None, facts_raw={}, ansible_version="2.9.27"
        )

        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)

        # Act
        response = self.client.post(
            reverse("frontend:ansible_result_apply", args=[result.pk])
        )

        # Assert
        assert response.status_code == 302

    @mock.patch("orthos2.data.models.AnsibleScanResult.apply_to_machine")
    def test_apply_handles_exception(self, mocked_apply: mock.MagicMock) -> None:
        """Should handle exception from apply_to_machine."""
        # Arrange
        mocked_apply.side_effect = Exception("Apply failed")

        machine = Machine.objects.first()
        result = AnsibleScanResult.objects.create(
            machine=machine, facts_raw={}, ansible_version="2.9.27"
        )

        superuser = User.objects.get(username="superuser")
        self.client.force_login(superuser)

        # Act
        response = self.client.post(
            reverse("frontend:ansible_result_apply", args=[result.pk])
        )

        # Assert
        assert response.status_code == 302


class MachineAnsibleResultsViewTest(WebTest):
    """Tests for machine_ansible_results view."""

    csrf_checks = True
    fixtures = [
        "orthos2/utils/tests/fixtures/machines.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
    ]

    def test_view_shows_machine_results(self) -> None:
        """Should show all results for a machine."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None

        for _ in range(3):
            AnsibleScanResult.objects.create(
                machine=machine, facts_raw={}, ansible_version="2.9.27"
            )

        # Act
        response = self.app.get(
            reverse("frontend:machine_ansible_results", args=[machine.pk]),
            user="superuser",
        )

        # Assert
        assert response.status_code == 200
        results = response.context["results"]
        assert len(results) == 3

    def test_view_pagination(self) -> None:
        """Should paginate results (20 per page)."""
        # Arrange
        machine = Machine.objects.first()
        assert machine is not None

        for _ in range(25):
            AnsibleScanResult.objects.create(
                machine=machine, facts_raw={}, ansible_version="2.9.27"
            )

        # Act
        response = self.app.get(
            reverse("frontend:machine_ansible_results", args=[machine.pk]),
            user="superuser",
        )

        # Assert
        assert response.status_code == 200
        results = response.context["results"]
        assert len(results) == 20  # paginate_by=20

    def test_view_nonexistent_machine(self) -> None:
        """Should return 404 for nonexistent machine."""
        # Act
        response = self.app.get(
            reverse("frontend:machine_ansible_results", args=[99999]),
            user="superuser",
            expect_errors=True,
        )

        # Assert
        assert response.status_code == 404
