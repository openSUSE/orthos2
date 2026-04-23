import logging
from typing import Any, List
from unittest import mock

from django.test import TestCase

import orthos2.utils.cobbler as cobbler
from orthos2.data.models import (
    Architecture,
    Domain,
    Machine,
    MachineGroup,
    RemotePowerDevice,
)

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
        self.assertIsNotNone(result)
        self.assertEqual(result.fqdn, test_machine.fqdn)  # type: ignore[union-attr]

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
            server.deploy_machines(machines)

            # Assert
            expected: List[Any] = []
            for exp in expected:
                self.assertIn(exp, mocked_update_or_add.mock_calls)

    def test_cobbler_deploy_remotepowerdevices(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        devices = RemotePowerDevice.objects.all()
        with mock.patch.object(
            cobbler.CobblerServer, "add_remote_power_device", return_value=None
        ) as mocked_add_remote_power_device, mock.patch.object(
            cobbler.CobblerServer, "remotepowerdevice_deployed", return_value=False
        ):
            server = cobbler.CobblerServer(domain)

            # Act
            server.deploy_remotepowerdevices(devices)

            # Assert
            for device in devices:
                mocked_add_remote_power_device.assert_any_call(
                    device, cobbler.CobblerSaveModes.NEW
                )

    def test_cobbler_add_remote_power_device(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = RemotePowerDevice.objects.get(fqdn="bmc.orthos2.test")

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "has_item", return_value=True  # type: ignore
        ) as mock_has_item, mock.patch.object(
            server._xmlrpc_server, "modify_system"  # type: ignore
        ) as mock_system_modify, mock.patch.object(
            server._xmlrpc_server, "save_system"  # type: ignore
        ) as mock_system_save, mock.patch.object(
            server._xmlrpc_server,  # type: ignore
            "new_system",
            return_value="system::bmc.orthos2.test",
        ) as mock_system_new:
            server.add_remote_power_device(testsys, save=cobbler.CobblerSaveModes.NEW)

            # Assert
            self.assertEqual(mock_has_item.call_count, 1)
            self.assertEqual(mock_system_new.call_count, 1)
            self.assertEqual(mock_system_modify.call_count, 4)
            self.assertEqual(mock_system_save.call_count, 1)

    def test_cobbler_remotepowerdevice_deployed(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = RemotePowerDevice.objects.get(fqdn="bmc.orthos2.test")

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "has_item", return_value=True  # type: ignore
        ) as mock_has_item:
            result = server.remotepowerdevice_deployed(testsys)

        # Assert
        self.assertTrue(result)
        mock_has_item.assert_called_once_with("system", testsys.fqdn, server._token)

    def test_cobbler_add_machine(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = Machine.objects.get(fqdn="testsys.orthos2.test")

        # Act
        with mock.patch(
            "orthos2.utils.cobbler.get_default_profile", return_value="default_profile"
        ) as mock_default_profile, mock.patch.object(
            server._xmlrpc_server, "has_item", return_value=True  # type: ignore
        ) as mock_has_item, mock.patch.object(
            server._xmlrpc_server, "modify_system"  # type: ignore
        ) as mock_system_modify, mock.patch.object(
            server._xmlrpc_server, "save_system"  # type: ignore
        ) as mock_system_save, mock.patch.object(
            server._xmlrpc_server,  # type: ignore
            "new_system",
            return_value="system::testsys.orthos2.test",
        ) as mock_system_new, mock.patch.object(
            server, "add_bmc"
        ) as mock_add_bmc, mock.patch.object(
            server, "add_power_options"
        ) as mock_add_power, mock.patch.object(
            server, "add_serial_console"
        ) as mock_add_serial, mock.patch.object(
            server, "add_network_interfaces"
        ) as mock_add_interface:
            server.add_machine(testsys, save=cobbler.CobblerSaveModes.NEW)

            # Assert
            self.assertEqual(mock_default_profile.call_count, 1)
            self.assertEqual(mock_has_item.call_count, 1)
            self.assertEqual(mock_system_new.call_count, 1)
            self.assertEqual(mock_system_modify.call_count, 5)
            self.assertEqual(mock_system_save.call_count, 1)
            self.assertEqual(mock_add_interface.call_count, 1)
            self.assertEqual(mock_add_bmc.call_count, 1)
            self.assertEqual(mock_add_power.call_count, 1)
            self.assertEqual(mock_add_serial.call_count, 1)

    def test_cobbler_add_network_interfaces(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = Machine.objects.get(fqdn="testsys.orthos2.test")
        object_id = "system::testsys.orthos2.test"

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "modify_system"  # type: ignore
        ) as mock_system_modify:
            server.add_network_interfaces(testsys, object_id)

            # Assert
            self.assertEqual(mock_system_modify.call_count, 2)

    def test_cobbler_add_bmc(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = Machine.objects.get(fqdn="testsys.orthos2.test")

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "modify_system"  # type: ignore
        ) as mock_system_modify:
            server.add_bmc(testsys, "system::testsys.orthos2.test")

            # Assert
            self.assertEqual(mock_system_modify.call_count, 1)

    def test_cobbler_add_serial_console(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = Machine.objects.get(fqdn="testsys.orthos2.test")

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "modify_system"  # type: ignore
        ) as mock_system_modify:
            server.add_serial_console(testsys, "system::testsys.orthos2.test")

            # Assert
            self.assertEqual(mock_system_modify.call_count, 2)

    def test_cobbler_add_power_options(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = Machine.objects.get(fqdn="testsys.orthos2.test")
        object_id = "system::testsys.orthos2.test"

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "modify_system"  # type: ignore
        ) as mock_system_modify:
            server.add_power_options(testsys, object_id)

            # Assert
            self.assertEqual(mock_system_modify.call_count, 4)

    def test_cobbler_set_netboot_state(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = Machine.objects.get(fqdn="testsys.orthos2.test")

        # Act
        with mock.patch.object(
            server._xmlrpc_server,  # type: ignore
            "get_system_handle",
            return_value="system::testsys.orthos2.test",
        ) as mock_system_handle:
            with mock.patch.object(
                server._xmlrpc_server, "modify_system"  # type: ignore
            ) as mock_system_modify:
                server.set_netboot_state(testsys, True)

                # Assert
                self.assertEqual(mock_system_handle.call_count, 1)
                self.assertEqual(mock_system_modify.call_count, 1)

    def test_cobbler_machine_deployed(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = Machine.objects.get(fqdn="testsys.orthos2.test")

        # Act
        result = server.machine_deployed(testsys)

        # Assert
        self.assertFalse(result)

    def test_cobbler_update_or_add(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = Machine.objects.get(fqdn="testsys.orthos2.test")

        # Act
        with mock.patch.object(server, "add_machine") as mock_add_machine:
            server.update_or_add(testsys)

            # Assert
            self.assertEqual(mock_add_machine.call_count, 1)
            mock_add_machine.assert_called_with(
                testsys, save=cobbler.CobblerSaveModes.NEW
            )

    def test_cobbler_remove(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        testsys = Machine.objects.get(fqdn="testsys.orthos2.test")

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "remove_system"  # type: ignore
        ) as mock_system_remove:
            server.remove(testsys)

            # Assert
            self.assertEqual(mock_system_remove.call_count, 1)

    def test_cobbler_remove_by_name(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        server._token = "token"  # type: ignore

        # Act
        with mock.patch.object(
            server, "is_running", return_value=True
        ), mock.patch.object(
            server._xmlrpc_server, "remove_system"  # type: ignore
        ) as mock_system_remove:
            server.remove_by_name("stale.orthos2.test")

            # Assert
            mock_system_remove.assert_called_once_with(
                "stale.orthos2.test", mock.ANY, False
            )

    def test_cobbler_remove_by_name_not_running(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)
        server._token = "token"  # type: ignore

        # Act/Assert
        with mock.patch.object(server, "is_running", return_value=False):
            self.assertRaises(
                cobbler.CobblerException,
                server.remove_by_name,
                "stale.orthos2.test",
            )

    def test_cobbler_prune_stale_dry_run(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        with mock.patch.object(
            server,
            "get_machines",
            return_value=["testsys.orthos2.test", "stale.orthos2.test"],
        ), mock.patch.object(server, "remove_by_name") as mock_remove_by_name:
            result = server.prune_stale({"testsys.orthos2.test"}, dry_run=True)

            # Assert
            self.assertEqual(result, ["stale.orthos2.test"])
            mock_remove_by_name.assert_not_called()

    def test_cobbler_prune_stale_removes(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        with mock.patch.object(
            server,
            "get_machines",
            return_value=["testsys.orthos2.test", "stale.orthos2.test"],
        ), mock.patch.object(server, "remove_by_name") as mock_remove_by_name:
            result = server.prune_stale({"testsys.orthos2.test"}, dry_run=False)

            # Assert
            self.assertEqual(result, ["stale.orthos2.test"])
            mock_remove_by_name.assert_called_once_with("stale.orthos2.test")

    def test_cobbler_prune_stale_no_stale(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        with mock.patch.object(
            server, "get_machines", return_value=["testsys.orthos2.test"]
        ), mock.patch.object(server, "remove_by_name") as mock_remove_by_name:
            result = server.prune_stale({"testsys.orthos2.test"}, dry_run=False)

            # Assert
            self.assertEqual(result, [])
            mock_remove_by_name.assert_not_called()

    def test_cobbler_prune_stale_foreign_domain_protected(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        with mock.patch.object(
            server,
            "get_machines",
            return_value=["testsys.orthos2.test", "other.foreign-domain.test"],
        ), mock.patch.object(server, "remove_by_name") as mock_remove_by_name:
            result = server.prune_stale({"testsys.orthos2.test"}, dry_run=False)

            # Assert
            self.assertEqual(result, [])
            mock_remove_by_name.assert_not_called()

    def test_cobbler_remove_bmc(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "modify_system"  # type: ignore
        ) as mock_system_modify:
            server.remove_bmc("system::testsys.orthos2.test")

            # Assert
            self.assertEqual(mock_system_modify.call_count, 1)

    def test_cobbler_remove_serial_console(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "modify_system"  # type: ignore
        ) as mock_system_modify:
            server.remove_serial_console("system::testsys.orthos2.test")

            # Assert
            self.assertEqual(mock_system_modify.call_count, 2)

    def test_cobbler_remove_power_options(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        with mock.patch.object(
            server._xmlrpc_server, "modify_system"  # type: ignore
        ) as mock_system_modify:
            server.remove_power_options("system::testsys.orthos2.test")

            # Assert
            self.assertEqual(mock_system_modify.call_count, 7)

    def test_cobbler_sync_dhcp(self) -> None:
        # Arrange
        domain = Domain.objects.get(name="orthos2.test")
        domain.cobbler_server = Machine.objects.get(fqdn="cobbler.orthos2.test")
        server = cobbler.CobblerServer(domain)

        # Act
        with mock.patch.object(server._xmlrpc_server, "sync_dhcp") as mock_sync_dhcp:  # type: ignore
            server.sync_dhcp()

            # Assert
            self.assertEqual(mock_sync_dhcp.call_count, 1)

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
        self.assertTrue(isinstance(profiles, list))  # type: ignore
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
