import logging
from unittest import mock

from django.test import TestCase

import orthos2.utils.cobbler as cobbler
from orthos2.data.models import Architecture, Domain, Machine, MachineGroup

logging.disable(logging.CRITICAL)


class CobblerMethodTests(TestCase):
    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    def test_get_default_profile(self) -> None:
        """
        get_default_profile should return a default profile attached to an architecture, or raise
        value error if there is none.
        """
        machine = mock.NonCallableMagicMock(spec_set=Machine)
        architecture = mock.NonCallableMagicMock(spec_set=Architecture)
        architecture.default_profile = "test_profile"
        machine.architecture = architecture
        self.assertEqual(cobbler.get_default_profile(machine), "test_profile")
        architecture.default_profile = None
        self.assertRaises(ValueError, cobbler.get_default_profile, machine)

    def test_get_filename(self) -> None:
        """
        get_filename should return the right filename attribute.

        Machine > Group > Architecture > None
        """
        machine = mock.NonCallableMagicMock(spec_set=Machine)
        machine.dhcp_filename = "machine"
        group = mock.NonCallableMagicMock(spec_set=MachineGroup)
        group.dhcp_filename = "group"
        machine.group = group
        architecture = mock.NonCallableMagicMock(spec_set=Architecture)
        architecture.dhcp_filename = "architecture"
        machine.architecture = architecture
        self.assertEqual(cobbler.get_filename(machine), "machine")
        machine.dhcp_filename = None
        self.assertEqual(cobbler.get_filename(machine), "group")
        group.dhcp_filename = None
        self.assertEqual(cobbler.get_filename(machine), "architecture")
        architecture.dhcp_filename = None
        self.assertIsNone(cobbler.get_filename(machine))

    def test_get_tftp_server(self) -> None:
        # Arrange
        test_machine = Machine.objects.get(pk=1)

        # Act
        result = cobbler.get_tftp_server(test_machine)

        # Assert
        self.longMessage = True
        self.assertEqual(result, test_machine.fqdn)

    def test_cobbler_is_running(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        running = server.is_running()

        # Assert
        self.assertTrue(running)

    def test_cobbler_get_profiles(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        profiles = server.get_profiles("x86_64")

        # Assert
        self.assertTrue(isinstance(profiles, list))
        self.assertEqual(len(profiles), 0)

    def test_cobbler_get_machines(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        machines = server.get_machines()

        # Assert
        self.assertEqual(machines, [])

    def test_cobbler_deploy(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        machines = Machine.objects.all()
        with mock.patch.object(
            cobbler.CobblerServer, "update_or_add", return_value=None
        ) as mocked_update_or_add:
            server = cobbler.CobblerServer(domain)

            # Act
            server.deploy(machines)

            # Assert
            expected = []  # type: ignore
            for exp in expected:
                self.assertIn(exp, mocked_update_or_add.mock_calls)
