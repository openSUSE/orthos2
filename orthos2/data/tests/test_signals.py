from unittest import mock

from django.test import TestCase

from orthos2.data.models import Machine
from orthos2.utils.cobbler import CobblerServer


class MachinePreDeleteSignalTests(TestCase):
    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    def test_delete_succeeds_when_cobbler_raises_oserror(self) -> None:
        """
        Deleting a machine must succeed even when Cobbler is unreachable.

        The pre_delete signal handler must catch OSError (and its subclasses such
        as ConnectionRefusedError) so that a network failure does not abort the
        database-level deletion.
        """
        machine = Machine.objects.get(fqdn="testsys.orthos2.test")
        machine_pk = machine.pk

        with mock.patch.object(
            CobblerServer,
            "remove",
            side_effect=OSError(101, "Network is unreachable"),
        ):
            machine.delete()

        self.assertFalse(Machine.objects.filter(pk=machine_pk).exists())

    def test_delete_succeeds_when_cobbler_not_configured(self) -> None:
        """
        Deleting a machine must succeed even when no Cobbler server is configured
        for the domain (CobblerServer.__init__ raises ValueError).
        """
        machine = Machine.objects.get(fqdn="testsys.orthos2.test")
        machine_pk = machine.pk

        with mock.patch(
            "orthos2.data.signals.CobblerServer",
            side_effect=ValueError("Cobbler Server not configured"),
        ):
            machine.delete()

        self.assertFalse(Machine.objects.filter(pk=machine_pk).exists())

    def test_delete_logs_warning_when_cobbler_raises_oserror(self) -> None:
        """
        When Cobbler is unreachable, a warning must be logged and must include
        the machine's FQDN.

        assertLogs cannot be used here because test_cobbler.py calls
        logging.disable(logging.CRITICAL) at module level, which silences
        all log records globally for the entire test session.  Mocking the
        logger directly is immune to that global flag.
        """
        machine = Machine.objects.get(fqdn="testsys.orthos2.test")

        with mock.patch.object(
            CobblerServer,
            "remove",
            side_effect=OSError(101, "Network is unreachable"),
        ), mock.patch("orthos2.data.signals.logger") as mock_logger:
            machine.delete()

        mock_logger.warning.assert_called_once()
        fqdn_in_args = any(
            "testsys.orthos2.test" in str(arg)
            for arg in mock_logger.warning.call_args.args
        )
        self.assertTrue(fqdn_in_args)
