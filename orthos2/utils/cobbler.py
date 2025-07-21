"""
Utility module that wraps functionality that is related to Cobbler. This is assuming that the used Cobbler server
has version 3.3.6 or newer.
"""

import enum
import logging
import time
import xmlrpc.client  # nosec: B411
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    Dict,
    Iterable,
    List,
    Optional,
    ParamSpec,
    TypeVar,
)

from django.template import Context, Template

from orthos2.utils.misc import get_hostname

if TYPE_CHECKING:
    from orthos2.data.models import Domain, Machine

logger = logging.getLogger("utils")


class CobblerSaveModes(enum.Enum):
    SKIP = ""
    """
    This mode skips saving the item.
    """
    NEW = "new"
    """
    This mode saves the item in case it was never added to Cobbler before.
    """
    BYPASS = "bypass"
    """
    This mode saves the item in case it was already added to Cobbler before.
    """


class CobblerException(Exception):
    pass


def get_default_profile(machine: "Machine") -> str:
    default = machine.architecture.default_profile
    if default:
        return default
    raise ValueError(
        "Machine {machine} has no default profile".format(machine=machine.fqdn)
    )


def get_tftp_server(machine: "Machine") -> Optional["Machine"]:
    """
    Return the corresponding tftp server attribute for the DHCP record.

    Machine > Group > Domain
    """

    if machine.tftp_server:
        server = machine.tftp_server
    elif machine.group and machine.group.tftp_server:
        server = machine.group.tftp_server
    elif machine.fqdn_domain.tftp_server:
        server = machine.fqdn_domain.tftp_server
    else:
        server = None
    return server


def get_filename(machine: "Machine") -> Optional[str]:
    """
    Return the corresponding filename attribute for the DHCP record.

    Machine > Group > Architecture > None
    """
    context = Context({"machine": machine})

    if machine.dhcp_filename:
        filename = machine.dhcp_filename
    elif machine.group and machine.group.dhcp_filename:
        filename = Template(machine.group.dhcp_filename).render(context)
    elif machine.architecture.dhcp_filename:
        filename = Template(machine.architecture.dhcp_filename).render(context)
    else:
        filename = None

    return filename


P = ParamSpec("P")
R = TypeVar("R")


def login_required(
    func: Callable[Concatenate["CobblerServer", P], R],
) -> Callable[Concatenate["CobblerServer", P], R]:
    """
    Decorator to ensure that the user is logged in. This only works for "CobblerServer".
    """

    # noinspection PyProtectedMember
    def wrapper(self: "CobblerServer", *args: P.args, **kwargs: P.kwargs) -> R:
        # type checkers don't support block level disable comments
        if not (
            self._token  # type: ignore[reportPrivateUsage]
            or self._xmlrpc_server.token_check(self._token)  # type: ignore[reportPrivateUsage]
        ):
            # Empty or invalid token.
            self._login()  # type: ignore[reportPrivateUsage]
        return func(self, *args, **kwargs)

    return wrapper


class CobblerServer:
    """
    A short-lived class that will execute a required task related to a machine and should be thrown away after the task
    has finished.
    """

    def __init__(self, domain: "Domain"):
        """
        Constructor for CobblerServer.

        :param domain: Domain object for the Cobbler server that should be talked to.
        """
        self._domain = domain
        cobbler_server = self._domain.cobbler_server
        if not cobbler_server:
            raise ValueError(
                f'Cobbler Server not configured for domain "{self._domain.name}"!'
            )
        self._cobbler_server = cobbler_server
        self._xmlrpc_server = xmlrpc.client.Server(
            f"http://{self._cobbler_server.fqdn}/cobbler_api"
        )
        # We ignore this line because this is just the initial value so the variable is not None.
        self._token = ""  # nosec B105

    def deploy(self, machines: Iterable["Machine"]) -> None:
        """
        Deploy or update all machines of a single Cobbler server.
        """
        for machine in machines:
            if self._domain.pk != machine.fqdn_domain.pk:
                logger.warning(
                    'Skipping machine "%s" since it doesn\'t belong to the domain of the Cobbler server "%s"!',
                    machine.fqdn,
                    self._domain.name,
                )
            try:
                self.update_or_add(machine)
            except xmlrpc.client.Fault as fault:
                logger.error(
                    "Deploying of machine %s failed with the following error: %s",
                    machine.fqdn,
                    fault.faultString,
                    exc_info=fault,
                )

    def _login(self) -> None:
        try:
            token = self._xmlrpc_server.login(
                self._domain.cobbler_server_username,
                self._domain.cobbler_server_password,
            )
            if isinstance(token, str):
                self._token = token
                return
            raise TypeError("Cobbler server returned incorrect data for token!")
        except xmlrpc.client.Fault as xmlrpc_fault:
            logger.error("Error logging in!", exc_info=xmlrpc_fault)

    @login_required
    def add_machine(
        self, machine: "Machine", save: CobblerSaveModes = CobblerSaveModes.SKIP
    ) -> None:
        """
        Add or update a machine. If the machine has a BMC, Remote Power or Serial Console add that as well.

        :param machine: Machine to be added or updated.
        :param save: Whether to save the machine or not.
        """
        old_machine_has_bmc = False
        old_machine_has_remote_power = False
        old_machine_has_serial_console = False
        default_profile = get_default_profile(machine)
        if not default_profile:
            raise CobblerException(
                "could not determine default profile for machine {machine}".format(
                    machine=machine.fqdn
                )
            )
        if not self._xmlrpc_server.has_item("profile", default_profile, self._token):
            raise CobblerException("default profile didn't exist on cobbler server")
        tftp_server = get_tftp_server(machine)
        kernel_options = machine.kernel_options if machine.kernel_options else ""

        if save == CobblerSaveModes.NEW:
            object_id = self._xmlrpc_server.new_system(self._token)
        else:
            object_id = self._xmlrpc_server.get_system_handle(machine.fqdn, self._token)
            old_machine_dict = self._get_cobbler_datastructure(machine)
            if "bmc" in old_machine_dict.get("interfaces", {}):
                old_machine_has_bmc = True
            if (
                old_machine_dict.get("serial_device", -1) > -1
                and old_machine_dict.get("serial_baud_rate", -1) > -1
            ):
                old_machine_has_serial_console = True
            if old_machine_dict.get("power_type", "") != "":
                old_machine_has_remote_power = True
        if not isinstance(object_id, str):
            raise TypeError("Cobbler System ID must be a string!")
        self._xmlrpc_server.modify_system(object_id, "name", machine.fqdn, self._token)
        self._xmlrpc_server.modify_system(
            object_id, "profile", default_profile, self._token
        )

        self.add_network_interfaces(machine, object_id)
        self._xmlrpc_server.modify_system(
            object_id, "filename", get_filename(machine) or "", self._token
        )
        if tftp_server:
            if tftp_server.ip_address_v4:
                self._xmlrpc_server.modify_system(
                    object_id, "next_server_v4", tftp_server.ip_address_v4, self._token
                )
            if tftp_server.ip_address_v6:
                self._xmlrpc_server.modify_system(
                    object_id, "next_server_v6", tftp_server.ip_address_v6, self._token
                )
        if old_machine_has_bmc and not machine.has_bmc():
            self.remove_bmc(object_id, save)
        if machine.has_bmc():
            self.add_bmc(machine, object_id)
        if old_machine_has_remote_power and not machine.has_remotepower():
            self.remove_power_options(object_id, save)
        if machine.has_remotepower():
            self.add_power_options(machine, object_id)
        if old_machine_has_serial_console and not machine.has_serialconsole():
            self.remove_serial_console(object_id, save)
        if machine.has_serialconsole():
            self.add_serial_console(machine, object_id)
        self._xmlrpc_server.modify_system(
            object_id, "kernel_options", kernel_options, self._token
        )

        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(object_id, self._token, save.value)

    @login_required
    def add_network_interfaces(
        self,
        machine: "Machine",
        object_id: str,
        save: CobblerSaveModes = CobblerSaveModes.SKIP,
    ) -> None:
        """
        Add the primary network interface of the machine to Cobbler.

        :param machine: Machine that should be added or updated.
        :param object_id: ID of object to be added.
        :param save: Whether to save the machine or not.
        """
        for idx, intf in enumerate(
            machine.networkinterfaces.filter(primary_mac_address__isnull=False)
        ):
            ipv4s = intf.ip_addresses.filter(protocol="IPv4")
            ipv6s = intf.ip_addresses.filter(protocol="IPv6")
            if ipv4s.count() > 1 or ipv6s.count() > 1:
                logger.info(
                    "%s: Skipping interface %s because it has more then a single IPv4 or IPv6 address",
                    machine.fqdn,
                    intf.name,
                )
                continue

            if ipv4s.count() == 0 and ipv6s.count() == 0:
                logger.info(
                    "%s: Skipping interface %s because it has neither IPv4 nor IPv6 addresses",
                    machine.fqdn,
                    intf.name,
                )
                continue

            interface_key = "default" if intf.primary else idx

            interface_options = {
                f"macaddress-{interface_key}": intf.mac_address,
                f"ipaddress-{interface_key}": intf.ip_address_v4 or "",
                f"ipv6address-{interface_key}": intf.ip_address_v6 or "",
                f"management-{interface_key}": True,
            }

            if intf.primary:
                interface_options[f"hostname-{interface_key}"] = get_hostname(
                    machine.fqdn
                )
                interface_options[f"dnsname-{interface_key}"] = machine.fqdn

            self._xmlrpc_server.modify_system(
                object_id, "modify_interface", interface_options, self._token
            )

        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(object_id, self._token, save.value)

    @login_required
    def add_bmc(
        self,
        machine: "Machine",
        object_id: str,
        save: CobblerSaveModes = CobblerSaveModes.SKIP,
    ) -> None:
        """
        Add the BMC of the machine to Cobbler.

        :param machine: Machine that should be added or updated.
        :param object_id: ID of object to be added.
        :param save: Whether to save the machine or not.
        """
        bmc = machine.bmc
        interface_options = {
            "interfacetype-bmc": "bmc",
            "macaddress-bmc": bmc.mac,
            "hostname-bmc": get_hostname(bmc.fqdn),
            "dnsname-bmc": bmc.fqdn,
        }
        ipv4_address = bmc.ip_address_v4
        if ipv4_address is not None:
            interface_options["ipaddress-bmc"] = ipv4_address
        ipv6_address = bmc.ip_address_v6
        if ipv6_address is not None:
            interface_options["ipv6address-bmc"] = ipv6_address
        self._xmlrpc_server.modify_system(
            object_id, "modify_interface", interface_options, self._token
        )
        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(object_id, self._token, save.value)

    @login_required
    def add_serial_console(
        self,
        machine: "Machine",
        object_id: str,
        save: CobblerSaveModes = CobblerSaveModes.SKIP,
    ) -> None:
        """
        Add the Serial Console of the machine to Cobbler.

        :param machine: Machine that should be added or updated.
        :param object_id: ID of object to be added.
        :param save: Whether to save the machine or not.
        """
        console = machine.serialconsole

        self._xmlrpc_server.modify_system(
            object_id, "serial_device", console.kernel_device_num, self._token
        )
        self._xmlrpc_server.modify_system(
            object_id, "serial_baud_rate", console.baud_rate, self._token
        )
        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(object_id, self._token, save.value)

    @login_required
    def add_power_options(
        self,
        machine: "Machine",
        object_id: str,
        save: CobblerSaveModes = CobblerSaveModes.SKIP,
    ) -> None:
        """
        Add the out-of-band power management of the machine to Cobbler.

        :param machine: Machine that should be added or updated.
        :param object_id: ID of object to be added.
        :param save: Whether to save the machine or not.
        """
        remotepower = machine.remotepower
        fence = remotepower.get_remotepower_fence()

        self._xmlrpc_server.modify_system(
            object_id, "power_type", fence.name, self._token
        )

        if fence.identity_file == "":
            username, password = remotepower.get_credentials()
            self._xmlrpc_server.modify_system(
                object_id, "power_user", username, self._token
            )
            self._xmlrpc_server.modify_system(
                object_id, "power_pass", password, self._token
            )
        else:
            self._xmlrpc_server.modify_system(
                object_id, "power_user", fence.username, self._token
            )
            self._xmlrpc_server.modify_system(
                object_id, "power_identity_file", fence.identity_file, self._token
            )

        if fence.use_hostname_as_port:
            # The following is ignored since at runtime we will always have a hostname dynamically added.
            self._xmlrpc_server.modify_system(
                object_id, "power_id", get_hostname(machine.hostname), self._token  # type: ignore
            )
        elif fence.use_port:
            # Temporary workaround until fence raritan accepts port as --plug param
            if fence.name == "raritan":
                self._xmlrpc_server.modify_system(
                    object_id,
                    "power_id",
                    f"system1/outlet{remotepower.port}",
                    self._token,
                )
            else:
                self._xmlrpc_server.modify_system(
                    object_id, "power_id", remotepower.port, self._token
                )

        self._xmlrpc_server.modify_system(
            object_id, "power_address", remotepower.get_power_address(), self._token
        )
        if remotepower.options != "":
            self._xmlrpc_server.modify_system(
                object_id, "power_options", remotepower.options, self._token
            )

        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(object_id, self._token, save.value)

    @login_required
    def _get_cobbler_datastructure(self, machine: "Machine") -> Dict[str, Any]:
        """
        Get a Cobbler system struct.

        :param machine: Machine that should be retrieved.
        """
        system_dict = self._xmlrpc_server.get_system(
            machine.fqdn, False, False, self._token
        )
        if not isinstance(system_dict, dict):
            raise ValueError(
                "Cobbler Server didn't return a dictionary for system %s" % machine.fqdn
            )
        return system_dict

    @login_required
    def set_netboot_state(
        self,
        machine: "Machine",
        netboot_state: bool,
        save: CobblerSaveModes = CobblerSaveModes.SKIP,
    ) -> None:
        """
        Enable or disable the netboot state.

        :param machine: Machine that should be enabled/disabled.
        :param netboot_state: Whether to enable or disable the netboot state.
        :param save: Whether to save the machine or not.
        """
        system_handle = self._xmlrpc_server.get_system_handle(machine.fqdn, self._token)
        self._xmlrpc_server.modify_system(
            system_handle, "netboot_enabled", netboot_state, self._token
        )
        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(system_handle, self._token, save.value)

    @login_required
    def machine_deployed(self, machine: "Machine") -> bool:
        """
        Method to signal if a machine has been deployed.

        :returns: True in case the machine is present by its FQDN in Cobbler, otherwise False.
        """
        has_item = self._xmlrpc_server.has_item("system", machine.fqdn, self._token)
        if not isinstance(has_item, bool):
            raise TypeError(
                'Return value if machine "%s" is deployed must be of type bool!'
                % machine.fqdn
            )
        return has_item

    def update_or_add(self, machine: "Machine") -> None:
        """
        Add or update a given machine to a Cobbler server.

        :machine: The machine to be added or updated.
        """
        if machine.fqdn in self.get_machines():
            self.add_machine(machine, save=CobblerSaveModes.BYPASS)
        else:
            self.add_machine(machine, save=CobblerSaveModes.NEW)

    @login_required
    def remove(self, machine: "Machine") -> None:
        """
        Remove a given machine from a Cobbler server.

        :param machine: Machine to be removed.
        """
        if not self.is_running():
            raise CobblerException(
                "Cobbler server is not running: {}".format(self._cobbler_server.fqdn)
            )
        try:
            self._xmlrpc_server.remove_system(machine.fqdn, self._token, False)
        except xmlrpc.client.Fault as xmlrpc_fault:
            logging.error(
                'Removing %s failed with "%s"',
                machine.fqdn,
                xmlrpc_fault.faultString,
            )

    @login_required
    def remove_bmc(
        self, object_id: str, save: CobblerSaveModes = CobblerSaveModes.SKIP
    ) -> None:
        """
        Remove the virtual network interface that is present to represent the out-of-band management.

        :param object_id: ID of object to be added.
        :param save: Whether to save the machine or not.
        """
        self._xmlrpc_server.modify_system(
            object_id, "delete_interface", "bmc", self._token
        )
        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(object_id, self._token, save.value)

    @login_required
    def remove_serial_console(
        self, object_id: str, save: CobblerSaveModes = CobblerSaveModes.SKIP
    ) -> None:
        """
        Remove the options that are representing the serial console kernel options.

        :param object_id: ID of object to be added.
        :param save: Whether to save the machine or not.
        """
        self._xmlrpc_server.modify_system(object_id, "serial_device", -1, self._token)
        self._xmlrpc_server.modify_system(
            object_id, "serial_baud_rate", -1, self._token
        )
        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(object_id, self._token, save.value)

    @login_required
    def remove_power_options(
        self, object_id: str, save: CobblerSaveModes = CobblerSaveModes.SKIP
    ) -> None:
        """
        Remove the options that are allowing for remote power operations.

        :param object_id: ID of object to be added.
        :param save: Whether to save the machine or not.
        """
        self._xmlrpc_server.modify_system(object_id, "power_type", "", self._token)
        self._xmlrpc_server.modify_system(object_id, "power_user", "", self._token)
        self._xmlrpc_server.modify_system(
            object_id, "power_identity_file", "", self._token
        )
        self._xmlrpc_server.modify_system(object_id, "power_pass", "", self._token)
        self._xmlrpc_server.modify_system(object_id, "power_id", "", self._token)
        self._xmlrpc_server.modify_system(object_id, "power_address", "", self._token)
        self._xmlrpc_server.modify_system(object_id, "power_options", "", self._token)
        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(object_id, self._token, save.value)

    @login_required
    def sync_dhcp(self) -> None:
        """
        Synchronize the DHCP server configuration on the Cobbler server.
        """
        if not self.is_running():
            raise CobblerException(
                "Cobbler server is not running: {}".format(self._cobbler_server.fqdn)
            )
        try:
            self._xmlrpc_server.sync_dhcp(self._token)
        except xmlrpc.client.Fault as xmlrpc_fault:
            logging.error(
                "Dhcp sync on %s failed with exception: %s",
                self._cobbler_server.fqdn,
                xmlrpc_fault,
            )

    def is_running(self) -> bool:
        """
        Check if the Cobbler daemon is running via the cobbler ping command.

        :returns: True if the Cobbler daemon is running, otherwise False.
        """
        try:
            self._xmlrpc_server.ping()
        except xmlrpc.client.Fault:
            return False
        return True

    @login_required
    def get_profiles(self, architecture: str) -> List[str]:
        """
        Get all profiles for a given architecture. This assumes that the architecture is part of the profile name
        prefix in Cobbler.

        :param architecture: Architecture name.
        """
        found_profiles = self._xmlrpc_server.find_profile(
            {"name": architecture + "*"}, False, self._token
        )
        if not isinstance(found_profiles, list):
            raise TypeError(
                'Cobbler server returned incorrect data type for searching of profiles of architecture "%s"'
                % architecture
            )
        return found_profiles

    def get_machines(self) -> List[str]:
        """
        Get the names of all machines. A machine corresponds to a single Cobbler System.
        """
        if not self.is_running():
            raise CobblerException(
                "Cobbler server is not running: {}".format(self._cobbler_server.fqdn)
            )
        item_names = self._xmlrpc_server.get_item_names("system")
        if not isinstance(item_names, list):
            raise TypeError(
                "Cobbler server returned incorrect data type for searching of items of type system"
            )
        return item_names

    @login_required
    def setup(self, machine: "Machine", choice: str) -> None:
        """
        Setup a machine with a given Cobbler profile.

        :machine: Machine to setup.
        :choice: Cobbler profile name.
        """
        logger.info(
            "setup called for %s with %s on cobbler server %s ",
            machine.fqdn,
            self._cobbler_server.fqdn,
            choice,
        )
        object_id = self._xmlrpc_server.get_system_handle(machine.fqdn, self._token)
        if choice:
            self._xmlrpc_server.modify_system(
                object_id, "profile", f"{machine.architecture}:{choice}", self._token
            )

        self.set_netboot_state(machine, True)
        self._xmlrpc_server.save_system(object_id, self._token, "bypass")

    @login_required
    def powerswitch(self, machine: "Machine", action: str) -> str:
        if not self.is_running():
            raise CobblerException(
                "Cobbler server is not running: {}".format(self._cobbler_server.fqdn)
            )

        logger.debug("powerswitching of %s called with action %s", machine.fqdn, action)
        background_power_options = {"systems": [machine.fqdn], "power": action}
        task_id = self._xmlrpc_server.background_power_system(
            background_power_options, self._token
        )
        if not isinstance(task_id, str):
            raise TypeError("Background power system returned incorrect data type")
        try:
            max_tries = 30
            tries = 0
            # Below code cannot be type checked since we don't want to save the data to a
            # variable and the XML-RPC API doesn't know what type the other end will return.
            while self.__get_task_status(task_id) == "running" and tries < max_tries:
                tries += 1
                logger.debug("Waiting for power task to finish (%s)", tries)
                time.sleep(2)
            event_log = self._xmlrpc_server.get_event_log(task_id)
            if not isinstance(event_log, str):
                raise TypeError(
                    "Cobbler Server returned incorrect data type for event log"
                )
            return event_log
        except xmlrpc.client.Fault as xmlrpc_fault:
            logger.warning(
                "Powerswitching of %s with %s failed on %s",
                machine.fqdn,
                action,
                self._cobbler_server.fqdn,
            )
            raise CobblerException(
                "Powerswitching of {machine} with {command} failed on {server} with {error}".format(
                    machine=machine.fqdn,
                    command=action,
                    server=self._cobbler_server.fqdn,
                    error=xmlrpc_fault.faultString,
                )
            ) from xmlrpc_fault

    def __get_task_status(self, event_id: str) -> str:
        """
        Wrapper method to have a type safe way to check the event status.

        :param event_id: The event ID to query the API for.
        :returns: A normalized version of the current event status.
        """
        event_result_obj = self._xmlrpc_server.get_task_status(event_id)
        if not isinstance(event_result_obj, list):
            raise TypeError(
                "Cobbler server returned incorrect data type for event result"
            )
        event_status = event_result_obj[2]
        if not isinstance(event_status, str):
            raise TypeError(
                "Cobbler Server returned incorrect data type for event status"
            )
        if event_status == "notification":
            # This is a bug that Cobbler has in the 3.3.7 release.
            return "running"
        return event_status
