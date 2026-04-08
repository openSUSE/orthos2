from unittest import mock

from django.test import TestCase

from orthos2.data.models import Machine


class DeactivateSolMachineTest(TestCase):

    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    @mock.patch("orthos2.data.signals.signal_serialconsole_sol_deactivate.send")
    def test_deactivate_sol_enqueues_task(self, mocked_send: mock.MagicMock) -> None:
        """The model action should enqueue a task instead of running SOL deactivate inline."""

        machine = Machine.objects.get(pk=2)
        machine.fqdn_domain.__class__.objects.filter(pk=machine.fqdn_domain.pk).update(
            cscreen_server=machine
        )
        machine.refresh_from_db()

        result = machine.deactivate_sol()

        self.assertTrue(result)
        mocked_send.assert_called_once_with(
            sender=Machine,
            machine_id=machine.pk,
        )

    def test_deactivate_sol_requires_serialconsole(self) -> None:
        """The model action should return False when no serial console is configured."""

        machine = Machine.objects.get(pk=1)

        self.assertFalse(machine.deactivate_sol())

    def test_deactivate_sol_requires_cscreen_server(self) -> None:
        """The model action should return False when no serial console server is configured."""
        machine = Machine.objects.get(pk=2)

        self.assertFalse(machine.deactivate_sol())
