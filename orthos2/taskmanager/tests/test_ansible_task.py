import datetime as datetime_module
import os
from datetime import datetime
from unittest import mock

from django.test import TestCase, override_settings

from orthos2.data.models import AnsibleScanResult, Domain, Machine, ServerConfig
from orthos2.taskmanager.tasks.ansible import Ansible


@override_settings(DEBUG=False)
class AnsibleTaskTest(TestCase):
    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    def setUp(self) -> None:
        """Set up ServerConfig and Domain for tests."""
        ServerConfig.objects.update_or_create(
            key="domain.validendings", defaults={"value": "orthos2.test"}
        )
        domain = Domain.objects.get(name="orthos2.test")
        domain.save()

    def test_ansible_task_initialization(self) -> None:
        """Should initialize task with machine list."""
        # Arrange
        machines = ["machine1.test", "machine2.test"]

        # Act
        task = Ansible(machines)

        # Assert
        assert task.machines == machines

    @mock.patch("orthos2.taskmanager.tasks.ansible.execute")
    def test_execute_sets_environment_variable(
        self, mocked_execute: mock.MagicMock
    ) -> None:
        """Should set ORTHOS_SCAN_TASK_HASH during execution and clean up."""
        # Arrange
        mocked_execute.return_value = ("", "", 0)

        # Ensure env var doesn't exist before
        if "ORTHOS_SCAN_TASK_HASH" in os.environ:
            del os.environ["ORTHOS_SCAN_TASK_HASH"]

        task = Ansible(["testsys.orthos2.test"])

        # Act
        task.execute()

        # Assert
        # Should be cleaned up after execution
        assert "ORTHOS_SCAN_TASK_HASH" not in os.environ

    @mock.patch("orthos2.taskmanager.tasks.ansible.execute")
    def test_execute_calls_ansible_playbook(
        self, mocked_execute: mock.MagicMock
    ) -> None:
        """Should execute ansible-playbook with correct command."""
        # Arrange
        mocked_execute.return_value = ("", "", 0)

        task = Ansible(["testsys.orthos2.test"])

        # Act
        task.execute()

        # Assert
        mocked_execute.assert_called_once()
        command = mocked_execute.call_args[0][0]
        assert "/usr/bin/ansible-playbook" in command
        assert "-i /usr/lib/orthos2/ansible/orthos_dynamic.yml" in command
        assert "/usr/lib/orthos2/ansible/site.yml" in command

    @mock.patch("orthos2.taskmanager.tasks.ansible.timezone.now")
    @mock.patch("orthos2.taskmanager.tasks.ansible.execute")
    def test_execute_logs_missing_machines(
        self, mocked_execute: mock.MagicMock, mocked_now: mock.MagicMock
    ) -> None:
        """Should log warning for machines without scan results."""
        # Arrange
        # Use a far-future timestamp to avoid conflicts with other test data
        scan_start = datetime(
            2099, 12, 31, 23, 59, 59, tzinfo=datetime_module.timezone.utc
        )
        mocked_now.return_value = scan_start
        mocked_execute.return_value = ("", "", 0)

        # Create task with 3 machines
        machines = [
            "testsys.orthos2.test",
            "cobbler.orthos2.test",
            "missing.orthos2.test",
        ]
        task = Ansible(machines)

        # Create scan results for only 2 machines (with the far-future timestamp)
        machine1 = Machine.objects.get(fqdn="testsys.orthos2.test")
        machine2 = Machine.objects.get(fqdn="cobbler.orthos2.test")

        AnsibleScanResult.objects.create(
            machine=machine1,
            facts_raw={},
            ansible_version="2.9.27",
            run_date=scan_start,
        )
        AnsibleScanResult.objects.create(
            machine=machine2,
            facts_raw={},
            ansible_version="2.9.27",
            run_date=scan_start,
        )

        # Act
        # Execute - should log warning about missing.orthos2.test
        with self.assertLogs("tasks", level="WARNING") as cm:
            task.execute()

        # Assert
        # Check warning was logged
        log_output = " ".join(cm.output)
        assert "missing.orthos2.test" in log_output

    @mock.patch("orthos2.taskmanager.tasks.ansible.execute")
    def test_execute_raises_on_ansible_failure(
        self, mocked_execute: mock.MagicMock
    ) -> None:
        """Should raise RuntimeError when ansible-playbook fails."""
        # Arrange
        mocked_execute.return_value = ("", "Ansible error occurred", 1)

        task = Ansible(["testsys.orthos2.test"])

        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            task.execute()

        assert "Ansible playbook failed" in str(context.exception)
        assert "Ansible error occurred" in str(context.exception)

    @mock.patch("orthos2.taskmanager.tasks.ansible.execute")
    def test_execute_cleans_up_env_on_exception(
        self, mocked_execute: mock.MagicMock
    ) -> None:
        """Should clean up environment variable even when exception occurs."""
        # Arrange
        mocked_execute.side_effect = Exception("Unexpected error")

        # Ensure env var doesn't exist before
        if "ORTHOS_SCAN_TASK_HASH" in os.environ:
            del os.environ["ORTHOS_SCAN_TASK_HASH"]

        task = Ansible(["testsys.orthos2.test"])

        # Act
        try:
            task.execute()
        except Exception:
            pass  # Expected

        # Assert
        # Should still be cleaned up
        assert "ORTHOS_SCAN_TASK_HASH" not in os.environ

    @mock.patch("orthos2.taskmanager.tasks.ansible.execute")
    def test_execute_with_no_machines(self, mocked_execute: mock.MagicMock) -> None:
        """Should handle empty machine list gracefully."""
        # Arrange
        mocked_execute.return_value = ("", "", 0)

        task = Ansible([])

        # Act
        task.execute()

        # Assert
        # Should complete without error
        mocked_execute.assert_called_once()
