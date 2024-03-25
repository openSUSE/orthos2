import logging

import mock
from django.test import TestCase
from mock import MagicMock, NonCallableMagicMock

import orthos2.utils.cobbler as cobbler
from orthos2.data.models import Architecture, Domain, Machine, MachineGroup, RemotePower
from orthos2.utils.cobbler import CobblerException

logging.disable(logging.CRITICAL)


class CobblerMethodTests(TestCase):
    fixtures = ["orthos2/utils/tests/fixtures/machines.json"]

    def test_get_default_profile(self):
        """
        get_default_profile should return a default profile attached to an architecture, or raise
        value error if there is none.
        """
        machine = NonCallableMagicMock(spec_set=Machine)
        architecture = NonCallableMagicMock(spec_set=Architecture)
        architecture.default_profile = "test_profile"
        machine.architecture = architecture
        self.assertEqual(cobbler.get_default_profile(machine), "test_profile")
        architecture.default_profile = None
        self.assertRaises(ValueError, cobbler.get_default_profile, machine)

    def test_get_filename(self):
        """
        get_filename should return the right filename attribute.

        Machine > Group > Architecture > None
        """
        machine = NonCallableMagicMock(spec_set=Machine)
        machine.dhcp_filename = "machine"
        group = NonCallableMagicMock(spec_set=MachineGroup)
        group.dhcp_filename = "group"
        machine.group = group
        architecture = NonCallableMagicMock(spec_set=Architecture)
        architecture.dhcp_filename = "architecture"
        machine.architecture = architecture
        self.assertEqual(cobbler.get_filename(machine), "machine")
        machine.dhcp_filename = None
        self.assertEqual(cobbler.get_filename(machine), "group")
        group.dhcp_filename = None
        self.assertEqual(cobbler.get_filename(machine), "architecture")
        architecture.dhcp_filename = None
        self.assertIsNone(cobbler.get_filename(machine))

    def test_get_tftp_server(self):
        # Arrange
        test_machine = Machine.objects.get(pk=1)

        # Act
        result = cobbler.get_tftp_server(test_machine)

        # Assert
        self.longMessage = True
        self.assertEqual(result, test_machine.fqdn)

    def test_get_bmc_command(self):
        # Arrange
        test_machine = Machine.objects.get(pk=1)

        # Act
        result = cobbler.get_bmc_command(test_machine, "cobbler")

        # Assert
        self.assertEqual(
            result,
            'cobbler system edit'
            ' --name=test.foo.bar.de'
            ' --interface=bmc'
            ' --interface-type=bmc'
            ' --ip-address=""'
            ' --mac=""'
            ' --dns-name="my-bmc"'
            ' --ipv6-address="" '
        )

    def test_get_power_options(self):
        # Arrange
        test_machine = Machine.objects.get(pk=1)
        test_machine.remotepower = RemotePower.objects.get(pk=1)
        remote_power_types = [
            {
                'fence': 'ipmilanplus',
                'device': 'rpower_device',
                'username': 'xxx',
                'password': 'XXX',
                'arch': ['x86_64', 'aarch64'],
                'system': ['Bare Metal']
            },
        ]

        # Act
        with self.settings(REMOTEPOWER_TYPES=remote_power_types):
            result = cobbler.get_power_options(test_machine)

        # Assert
        self.longMessage = True
        self.assertEqual(
            result,
            " --power-type=ipmilanplus  --power-user=test --power-pass=test  --power-address=rpower.foo.de"
        )

    @mock.patch(
        "orthos2.utils.cobbler.get_tftp_server",
        mock.MagicMock(return_value="--next-server=172.30.0.1"),
    )
    @mock.patch(
        "orthos2.utils.cobbler.get_power_options",
        mock.MagicMock(return_value="--power-options"),
    )
    def test_create_cobbler_options(self):
        # Arrange
        test_machine = Machine.objects.get(pk=1)
        test_machine.mac_address = "AA:BB:CC:DD:EE:FF"

        # Act
        with mock.patch("orthos2.data.models.Machine.ipv4", new_callable=mock.PropertyMock(return_value="17.17.17.17")):
            options = cobbler.create_cobbler_options(test_machine)

        # Assert
        self.longMessage = True
        self.assertTrue(" --name=test.foo.bar" in options)
        self.assertTrue(" --ip-address=17.17.17.17" in options)
        self.assertTrue(" --ipv6-address=" in options)
        self.assertTrue(" --interface=default" in options)
        self.assertTrue(" --management=True" in options)
        self.assertTrue(" --interface-master=True" in options)

        # Act
        with mock.patch("orthos2.data.models.Machine.ipv6",
                        new_callable=mock.PropertyMock(return_value="2001:db8::8a2e:370:7334")):
            options = cobbler.create_cobbler_options(test_machine)

        # Assert
        self.assertTrue(" --ipv6-address=2001:db8::8a2e:370:7334" in options)

        # Arrange
        test_machine.dhcp_filename = "file.name"

        # Act
        with mock.patch("orthos2.data.models.Machine.ipv6",
                        new_callable=mock.PropertyMock(return_value=None)):
            options = cobbler.create_cobbler_options(test_machine)

        # Assert
        self.assertTrue(" --ipv6-address=" in options)
        self.assertTrue(" --filename=file.name" in options)

        # Act
        with mock.patch("orthos2.data.models.Machine.ipv6",
                        new_callable=mock.PropertyMock(return_value="2001:db8::8a2e:370:7334")):
            options = cobbler.create_cobbler_options(test_machine)

        # Assert
        self.assertTrue(" --filename=file.name" in options)
        self.assertTrue(" --ipv6-address=2001:db8::8a2e:370:7334" in options)

    @mock.patch("orthos2.utils.cobbler.create_cobbler_options",
                mock.MagicMock(return_value="option-string"))
    @mock.patch("orthos2.utils.cobbler.get_default_profile", mock.MagicMock(return_value="default_profile"))
    def test_get_cobbler_add_command(self):
        machine = mock.NonCallableMock()
        path = "/cobbler/path"
        command = cobbler.get_cobbler_add_command(machine, path)
        self.assertTrue(command.startswith("/cobbler/path system add "))
        self.assertTrue("option-string" in command)
        self.assertTrue(" --profile=default_profile" in command)
        self.assertTrue("--netboot-enabled=False")

    @mock.patch("orthos2.utils.cobbler.create_cobbler_options",
                mock.MagicMock(return_value="option-string"))
    @mock.patch("orthos2.utils.cobbler.get_default_profile", mock.MagicMock(return_value="default_profile"))
    def test_get_cobbler_update_command(self):
        machine = mock.NonCallableMock()
        path = "/cobbler/path"
        command = cobbler.get_cobbler_update_command(machine, path)
        self.assertTrue(command.startswith("/cobbler/path system edit "))
        self.assertTrue("option-string" in command)

    def test_cobbler_is_installed(self):
        server = cobbler.CobblerServer("test.foo.bar", "foo.bar")
        server._cobbler_path = "/cobbler/path"
        conn = mock.NonCallableMock()
        conn.check_path.return_value = False
        server._conn = conn
        self.assertFalse(server.is_installed())
        expected = [mock.call.check_path("/cobbler/path", "-x")]
        self.assertEqual(expected, server._conn.mock_calls)
        server._conn.mock_calls = []
        server._conn.check_path.return_value = True
        self.assertTrue(server.is_installed())
        self.assertEqual(expected, server._conn.mock_calls)

    def test_cobbler_is_running(self):
        server = cobbler.CobblerServer("test.foo.bar", "foo.bar")
        server._cobbler_path = "/cobbler/path"
        conn = mock.NonCallableMock()
        conn.execute.return_value = [["Cobbler 3.1.2", "source: ?, ?",
                                      "build time: Mon Feb 24 12:00:00 2020"], "", 0]
        server._conn = conn
        running = server.is_running()
        self.assertTrue(running)
        expected = [mock.call.execute("/cobbler/path version")]
        self.assertEqual(expected, conn.mock_calls)
        conn.execute.return_value = ["", "cobblerd does not appear to be running/accessible: "
                                     "ConnectionRefusedError(111, 'Connection refused')", 155]
        running = server.is_running()
        self.assertFalse(running)

    def test_cobbler_get_machines(self):
        server = cobbler.CobblerServer("test.foo.bar", "foo.bar")
        server._cobbler_path = "/cobbler/path"
        conn = mock.NonCallableMagicMock()
        conn.execute.return_value = [["test1.foo.bar", "test2.foo.bar"], "", 0]
        server._conn = conn
        machines = server.get_machines()
        self.assertEqual(machines, ["test1.foo.bar", "test2.foo.bar"])
        expected = [mock.call.execute("/cobbler/path system list")]
        self.assertEqual(expected, server._conn.mock_calls)
        conn.execute.return_value = [["test1.foo.bar", "test2.foo.bar"], "", 1]
        self.assertRaises(cobbler.CobblerException, server.get_machines)

    machine1 = NonCallableMagicMock(spec_set=Machine)
    machine1.fqdn = "test1.foo.bar"
    machine2 = NonCallableMagicMock(spec_set=Machine)
    machine2.fqdn = "test2.foo.bar"

    def mocked_get_add_command(machine, _):
        return machine.fqdn + "-add"

    def mocked_get_update_command(machine, _):
        return machine.fqdn + "-update"

    @mock.patch("orthos2.data.models.Machine.active_machines.filter",
                MagicMock(return_value=[machine1, machine2]))
    @mock.patch("orthos2.utils.cobbler.CobblerServer.get_machines", MagicMock(return_value="test1.foo.bar"))
    @mock.patch("orthos2.utils.cobbler.get_bmc_command", MagicMock(return_value="cobbler system edit mock bmc command"))
    @mock.patch("orthos2.utils.cobbler.get_cobbler_update_command",
                MagicMock(side_effect=mocked_get_update_command))
    @mock.patch("orthos2.utils.cobbler.get_cobbler_add_command",
                MagicMock(side_effect=mocked_get_add_command))
    def test_cobbler_deploy(self):
        # Arrange
        domain = NonCallableMagicMock(spec_set=Domain)
        server = cobbler.CobblerServer("test.foo.bar", domain)
        server._cobbler_path = "/cobbler/path"
        conn = mock.NonCallableMagicMock()
        conn.execute.return_value = ["", "", 0]
        server._conn = conn
        server.is_running = mock.MagicMock(return_value=True)
        server.is_installed = mock.MagicMock(return_value=True)
        conn.mock_calls = []

        # Act
        server.deploy()

        # Assert
        expected = [mock.call.execute("test1.foo.bar-update"),
                    mock.call.execute("test2.foo.bar-add")]
        for exp in expected:
            self.assertIn(exp, conn.mock_calls)

    def test_cobbler_deploy_not_installed_not_running(self):
        # Arrange
        domain = NonCallableMagicMock(spec_set=Domain)
        server = cobbler.CobblerServer("test.foo.bar", domain)
        server._cobbler_path = "/cobbler/path"
        conn = mock.NonCallableMagicMock()
        conn.execute.return_value = ["", "", 0]
        server._conn = conn
        server.is_running = mock.MagicMock(return_value=False)
        server.is_installed = mock.MagicMock(return_value=False)

        # Act & Assert
        self.assertRaises(CobblerException, server.deploy)

    def test_cobbler_deploy_installed_not_running(self):
        # Arrange
        domain = NonCallableMagicMock(spec_set=Domain)
        server = cobbler.CobblerServer("test.foo.bar", domain)
        server._cobbler_path = "/cobbler/path"
        conn = mock.NonCallableMagicMock()
        conn.execute.return_value = ["", "", 0]
        server._conn = conn
        server.is_installed = mock.MagicMock(return_value=True)
        server.is_running = mock.MagicMock(return_value=False)

        # Act & Assert
        self.assertRaises(CobblerException, server.deploy)
