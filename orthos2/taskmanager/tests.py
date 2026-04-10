from unittest import mock

from django.test import TestCase

from orthos2.data.models import Machine
from orthos2.taskmanager.tasks.sol import DeactivateSerialOverLan


class DeactivateSerialOverLanTaskTest(TestCase):
    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    @mock.patch("orthos2.taskmanager.tasks.sol.SSH")
    def test_execute_runs_ipmitool_via_cscreen_server(
        self, mocked_ssh: mock.MagicMock
    ) -> None:
        """Task should execute SOL deactivation over SSH on the cscreen server."""

        machine = Machine.objects.get(pk=2)
        machine.fqdn_domain.__class__.objects.filter(pk=machine.fqdn_domain.pk).update(
            cscreen_server=machine
        )

        mocked_conn = mocked_ssh.return_value
        mocked_conn.execute.return_value = (["ok"], [], 0)

        task = DeactivateSerialOverLan(machine.pk)
        task.execute()

        mocked_ssh.assert_called_once_with(machine.fqdn)
        mocked_conn.connect.assert_called_once_with(user="_cscreen")
        mocked_conn.execute.assert_called_once()

        called_args = mocked_conn.execute.call_args.args
        called_kwargs = mocked_conn.execute.call_args.kwargs

        self.assertIn("/usr/bin/ipmitool", called_args[0])
        self.assertIn("-E", called_args[0])
        self.assertEqual(called_kwargs["timeout"], 30.0)
        self.assertEqual(called_kwargs["environment"]["IPMI_PASSWORD"], "root")
        mocked_conn.close.assert_called_once()

    @mock.patch("orthos2.taskmanager.tasks.sol.SSH")
    def test_execute_skips_when_no_cscreen_server(
        self, mocked_ssh: mock.MagicMock
    ) -> None:
        """Task should not attempt SSH when no serial console server is configured."""

        machine = Machine.objects.get(pk=2)
        machine.fqdn_domain.__class__.objects.filter(pk=machine.fqdn_domain.pk).update(
            cscreen_server=None
        )

        task = DeactivateSerialOverLan(machine.pk)
        task.execute()

        mocked_ssh.assert_not_called()
