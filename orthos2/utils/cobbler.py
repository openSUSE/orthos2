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
    Dict,
    Iterable,
    List,
    Optional,
    ParamSpec,
    TypeVar,
)

from django.template import Context, Template

from orthos2.utils.misc import get_hostname, get_ipv4, get_ipv6
from orthos2.utils.remotepowertype import RemotePowerType

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


def get_tftp_server(machine: "Machine") -> Optional[str]:
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
    return server.fqdn if server else None


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


def login_required(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to ensure that the user is logged in. This only works for "CobblerServer".
    """

    # noinspection PyProtectedMember
    def wrapper(*args, **kwargs):
        if not (args[0]._token or args[0]._xmlrpc_server.token_check(args[0]._token)):
            # Empty or invalid token.
            args[0]._login()
        return func(*args, **kwargs)

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

        object_id = self._xmlrpc_server.new_system(self._token)
        self._xmlrpc_server.modify_system(object_id, "name", machine.fqdn, self._token)
        self._xmlrpc_server.modify_system(
            object_id, "profile", default_profile, self._token
        )

        if machine.mac_address:
            self.add_primary_network_interface(machine)
        self._xmlrpc_server.modify_system(
            object_id, "filename", get_filename(machine) or "", self._token
        )
        if tftp_server:
            ipv4 = get_ipv4(tftp_server)
            if ipv4:
                self._xmlrpc_server.modify_system(
                    object_id, "next_server_v4", ipv4, self._token
                )
        if machine.has_bmc():
            self.add_bmc(machine)
        if machine.has_remotepower():
            self.add_power_options(machine)
        if machine.has_serialconsole():
            self.add_serial_console(machine)
        self._xmlrpc_server.modify_system(
            object_id, "kernel_options", kernel_options, self._token
        )

        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(object_id, self._token, save.value)

    @login_required
    def add_primary_network_interface(
        self, machine: "Machine", save: CobblerSaveModes = CobblerSaveModes.SKIP
    ) -> None:
        """
        Add the primary network interface of the machine to Cobbler.

        :param machine: Machine that should be added or updated.
        :param save: Whether to save the machine or not.
        """
        system_handle = self._xmlrpc_server.get_system_handle(machine.fqdn, self._token)
        interface_options = {
            "interfacemaster-default": True,
            "macaddress-default": machine.mac_address,
            "ipaddress-default": machine.ipv4 or "",
            "ipv6address-default": machine.ipv6 or "",
            "hostname-default": get_hostname(machine.fqdn),
            "dnsname-default": machine.fqdn,
            "management-default": True,
        }
        self._xmlrpc_server.modify_system(
            system_handle, "modify_interface", interface_options, self._token
        )
        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(system_handle, self._token, save.value)

    @login_required
    def add_bmc(
        self, machine: "Machine", save: CobblerSaveModes = CobblerSaveModes.SKIP
    ) -> None:
        """
        Add the BMC of the machine to Cobbler.

        :param machine: Machine that should be added or updated.
        :param save: Whether to save the machine or not.
        """
        bmc = machine.bmc
        system_handle = self._xmlrpc_server.get_system_handle(machine.fqdn, self._token)
        interface_options = {
            "interfacetype-bmc": "bmc",
            "macaddress-bmc": bmc.mac,
            "ipaddress-bmc": get_ipv4(bmc.fqdn),
            "ipv6address-bmc": get_ipv6(bmc.fqdn),
            "hostname-bmc": get_hostname(bmc.fqdn),
        }
        self._xmlrpc_server.modify_system(
            system_handle, "modify_interface", interface_options, self._token
        )
        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(system_handle, self._token, save.value)

    @login_required
    def add_serial_console(
        self, machine: "Machine", save: CobblerSaveModes = CobblerSaveModes.SKIP
    ) -> None:
        """
        Add the Serial Console of the machine to Cobbler.

        :param machine: Machine that should be added or updated.
        :param save: Whether to save the machine or not.
        """
        console = machine.serialconsole

        system_handle = self._xmlrpc_server.get_system_handle(machine.fqdn, self._token)
        self._xmlrpc_server.modify_system(
            system_handle, "serial_device", console.kernel_device_num, self._token
        )
        self._xmlrpc_server.modify_system(
            system_handle, "serial_baud_rate", console.baud_rate, self._token
        )
        if console.kernel_device != "None":
            system_dict = self._xmlrpc_server.get_system(machine.fqdn)
            if not isinstance(system_dict, dict):
                raise TypeError(
                    'System details for system "%s" must be a dict.' % machine.fqdn
                )
            current_kernel_options = system_dict.get("kernel_options", {})
            if not isinstance(current_kernel_options, (dict, str)):
                raise TypeError(
                    'Kernel options for system "%s" must be a dict or str.'
                    % machine.fqdn
                )
            if isinstance(current_kernel_options, str):
                if current_kernel_options == "<<inherit>>":
                    new_kernel_options: Dict[str, str] = {}
                else:
                    raise TypeError(
                        'Kernel options for system "%s" were neither inherit nor a dictionary.'
                        % machine.fqdn
                    )
            else:
                new_kernel_options = current_kernel_options.copy()
            new_kernel_options[
                "console"
            ] = f"{console.kernel_device}{console.kernel_device_num},{console.baud_rate}"
            self._xmlrpc_server.modify_system(
                system_handle, "kernel_options", new_kernel_options, self._token
            )
        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(system_handle, self._token, save.value)

    @login_required
    def add_power_options(
        self, machine: "Machine", save: CobblerSaveModes = CobblerSaveModes.SKIP
    ) -> None:
        """
        Add the out-of-band power management of the machine to Cobbler.

        :param machine: Machine that should be added or updated.
        :param save: Whether to save the machine or not.
        """
        remotepower = machine.remotepower
        fence = RemotePowerType.from_fence(remotepower.fence_name)
        if fence is None:
            raise ValueError(
                "Fence for machine %s couldn't be retrieved via RemotePowerType!"
                % machine.fqdn
            )
        system_handle = self._xmlrpc_server.get_system_handle(machine.fqdn, self._token)

        self._xmlrpc_server.modify_system(
            system_handle, "power_type", fence.fence, self._token
        )

        if fence.use_identity_file:
            self._xmlrpc_server.modify_system(
                system_handle, "power_user", fence.username, self._token
            )
            self._xmlrpc_server.modify_system(
                system_handle, "power_identity_file", fence.identity_file, self._token
            )
        else:
            username, password = remotepower.get_credentials()
            self._xmlrpc_server.modify_system(
                system_handle, "power_user", username, self._token
            )
            self._xmlrpc_server.modify_system(
                system_handle, "power_pass", password, self._token
            )

        if fence.use_hostname_as_port:
            # The following is ignored since at runtime we will always have a hostname dynamically added.
            self._xmlrpc_server.modify_system(
                system_handle, "power_id", get_hostname(machine.hostname), self._token  # type: ignore
            )
        elif fence.use_port:
            # Temporary workaround until fence raritan accepts port as --plug param
            if fence.fence == "raritan":
                self._xmlrpc_server.modify_system(
                    system_handle,
                    "power_id",
                    f"system1/outlet{remotepower.port}",
                    self._token,
                )
            else:
                self._xmlrpc_server.modify_system(
                    system_handle, "power_id", remotepower.port, self._token
                )

        self._xmlrpc_server.modify_system(
            system_handle, "power_address", remotepower.get_power_address(), self._token
        )
        if fence.use_options:
            self._xmlrpc_server.modify_system(
                system_handle, "power_options", remotepower.options, self._token
            )

        if save != CobblerSaveModes.SKIP:
            self._xmlrpc_server.save_system(system_handle, self._token, save.value)

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
        try:
            max_tries = 30
            tries = 0
            # Below code cannot be type checked since we don't want to save the data to a
            # variable and the XML-RPC API doesn't know what type the other end will return.
            while (
                self._xmlrpc_server.get_task_status(task_id)[2] == "running"  # type: ignore
                and tries < max_tries
            ):
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
