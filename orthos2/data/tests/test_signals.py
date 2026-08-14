from unittest import mock

from django.test import TestCase

from orthos2.data.models import Domain, Machine, RemotePowerDevice, ServerConfig
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


class RemotePowerDevicePreDeleteSignalTests(TestCase):
    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    def test_delete_succeeds_when_cobbler_raises_oserror(self) -> None:
        """
        Deleting a remote power device must succeed even when Cobbler is unreachable.

        The pre_delete signal handler must catch OSError (and its subclasses such
        as ConnectionRefusedError) so that a network failure does not abort the
        database-level deletion.
        """
        device = RemotePowerDevice.objects.get(fqdn="bmc.orthos2.test")
        device_pk = device.pk

        with mock.patch.object(
            CobblerServer,
            "remove_by_name",
            side_effect=OSError(101, "Network is unreachable"),
        ):
            device.delete()

        self.assertFalse(RemotePowerDevice.objects.filter(pk=device_pk).exists())

    def test_delete_succeeds_when_cobbler_not_configured(self) -> None:
        """
        Deleting a remote power device must succeed even when no Cobbler server is
        configured for the domain (CobblerServer.__init__ raises ValueError).
        """
        device = RemotePowerDevice.objects.get(fqdn="bmc.orthos2.test")
        device_pk = device.pk

        with mock.patch(
            "orthos2.data.signals.CobblerServer",
            side_effect=ValueError("Cobbler Server not configured"),
        ):
            device.delete()

        self.assertFalse(RemotePowerDevice.objects.filter(pk=device_pk).exists())

    def test_delete_logs_warning_when_cobbler_raises_oserror(self) -> None:
        """
        When Cobbler is unreachable, a warning must be logged and must include
        the device's FQDN.

        assertLogs cannot be used here because test_cobbler.py calls
        logging.disable(logging.CRITICAL) at module level, which silences
        all log records globally for the entire test session.  Mocking the
        logger directly is immune to that global flag.
        """
        device = RemotePowerDevice.objects.get(fqdn="bmc.orthos2.test")

        with mock.patch.object(
            CobblerServer,
            "remove_by_name",
            side_effect=OSError(101, "Network is unreachable"),
        ), mock.patch("orthos2.data.signals.logger") as mock_logger:
            device.delete()

        mock_logger.warning.assert_called_once()
        fqdn_in_args = any(
            "bmc.orthos2.test" in str(arg) for arg in mock_logger.warning.call_args.args
        )
        self.assertTrue(fqdn_in_args)


class MachineDomainChangeSignalTests(TestCase):
    """
    Changing a machine's fqdn_domain (i.e. changing its FQDN to one ending in a
    different, also-registered domain) must remove it from the *previous* domain's
    Cobbler server, so a stale entry doesn't linger there indefinitely - and that
    removal must never block the domain change itself if the old Cobbler server is
    unreachable or misconfigured.
    """

    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    def setUp(self) -> None:
        # This fixture (unlike orthos2/data/fixtures/tests/test_domain_orthos2test.json)
        # ships no "domain.validendings" ServerConfig entry, but both Domain.save() and
        # Machine.save() require one to exist before validating any FQDN/domain name.
        ServerConfig.objects.update_or_create(
            key="domain.validendings",
            defaults={"value": "orthos2.test,other.orthos2.test"},
        )
        Domain.objects.create(
            name="other.orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )

        # The fixture's "testsys.orthos2.test" has a BMC attached to a System that
        # doesn't allow one (Machine.save() enforces this), which would otherwise
        # block every save() below - irrelevant to what's being tested here.
        machine = Machine.objects.get(fqdn="testsys.orthos2.test")
        if machine.has_bmc():
            machine.bmc.delete()

    def test_domain_change_skips_signals_when_new_domain_cobbler_server_is_self(
        self,
    ) -> None:
        """
        If the machine being moved to a new domain *is* that domain's Cobbler
        server, it must not be added to Cobbler (a Cobbler server has no business
        managing itself as a system) and must not trigger a DHCP sync either.
        """
        machine = Machine.objects.get(fqdn="testsys.orthos2.test")
        new_domain = Domain.objects.get(name="other.orthos2.test")
        new_domain.cobbler_server = machine
        new_domain.save()

        with mock.patch(
            "orthos2.data.signals.signal_cobbler_machine_update.send"
        ) as mock_update_send, mock.patch(
            "orthos2.data.signals.signal_cobbler_sync_dhcp.send"
        ) as mock_sync_send:
            machine.fqdn = "testsys.other.orthos2.test"
            machine.save()

        mock_update_send.assert_not_called()
        mock_sync_send.assert_not_called()
        self.assertTrue(
            Machine.objects.filter(fqdn="testsys.other.orthos2.test").exists()
        )

    def _switch_machine_to_new_domain(self, machine: Machine) -> None:
        """Give the old domain a configured Cobbler server, then move the machine to
        the new domain - this is what actually exercises the old-domain removal code
        path in Machine.save()."""
        old_domain = machine.fqdn_domain
        old_domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        old_domain.save()

        # Re-fetch so Machine.__init__'s "_original" deep copy reflects the
        # just-persisted old_domain.cobbler_server.
        machine = Machine.objects.get(pk=machine.pk)
        machine.fqdn = "testsys.other.orthos2.test"
        machine.save()

    def test_domain_change_succeeds_when_old_cobbler_raises_oserror(self) -> None:
        """
        Changing a machine's domain must succeed even when the *previous* Cobbler
        server is unreachable.
        """
        machine = Machine.objects.get(fqdn="testsys.orthos2.test")

        with mock.patch.object(
            CobblerServer,
            "remove_by_name",
            side_effect=OSError(101, "Network is unreachable"),
        ) as mock_remove_by_name:
            self._switch_machine_to_new_domain(machine)

        mock_remove_by_name.assert_called_once_with("testsys.orthos2.test")
        self.assertTrue(
            Machine.objects.filter(fqdn="testsys.other.orthos2.test").exists()
        )

    def test_domain_change_succeeds_when_old_cobbler_not_configured(self) -> None:
        """
        Changing a machine's domain must succeed even when no Cobbler server is
        configured for the *previous* domain (CobblerServer.__init__ raises
        ValueError).
        """
        # Deliberately skip configuring old_domain.cobbler_server here.
        machine = Machine.objects.get(fqdn="testsys.orthos2.test")
        machine.fqdn = "testsys.other.orthos2.test"
        machine.save()

        self.assertTrue(
            Machine.objects.filter(fqdn="testsys.other.orthos2.test").exists()
        )

    def test_domain_change_logs_warning_when_old_cobbler_raises_oserror(self) -> None:
        """
        When the previous Cobbler server is unreachable, a warning must be logged
        and must include the machine's (old) FQDN.

        assertLogs cannot be used here because test_cobbler.py calls
        logging.disable(logging.CRITICAL) at module level, which silences all log
        records globally for the entire test session. Mocking the logger directly
        is immune to that global flag.
        """
        machine = Machine.objects.get(fqdn="testsys.orthos2.test")

        with mock.patch.object(
            CobblerServer,
            "remove_by_name",
            side_effect=OSError(101, "Network is unreachable"),
        ), mock.patch("orthos2.data.models.machine.logger") as mock_logger:
            self._switch_machine_to_new_domain(machine)

        mock_logger.warning.assert_called_once()
        fqdn_in_args = any(
            "testsys.orthos2.test" in str(arg)
            for arg in mock_logger.warning.call_args.args
        )
        self.assertTrue(fqdn_in_args)
