import datetime
import ipaddress
import logging
import re
from copy import deepcopy
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    Dict,
    List,
    Optional,
    ParamSpec,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from django.conf import settings
from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import models
from django.db.models import Q, QuerySet
from django.utils import timezone
from requests import HTTPError

from orthos2.data.exceptions import ReleaseException, ReserveException
from orthos2.data.models.architecture import Architecture
from orthos2.data.models.bmc import BMC
from orthos2.data.models.domain import Domain, DomainAdmin, validate_domain_ending
from orthos2.data.models.enclosure import Enclosure
from orthos2.data.models.machinegroup import MachineGroup
from orthos2.data.models.networkinterface import NetworkInterface, validate_mac_address
from orthos2.data.models.platform import Platform
from orthos2.data.models.remotepowertype import RemotePowerType
from orthos2.data.models.system import System
from orthos2.data.virtualization import VirtualizationAPI
from orthos2.data.virtualization.factory import virtualization_api_factory
from orthos2.utils.misc import (
    Serializer,
    get_domain,
    get_hostname,
    get_s390_hostname,
    is_dns_resolvable,
)
from orthos2.utils.netbox import Netbox

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from orthos2.data.models.annotation import Annotation
    from orthos2.data.models.bmc import BMC
    from orthos2.data.models.installation import Installation
    from orthos2.data.models.remotepower import RemotePower
    from orthos2.data.models.reservationhistory import ReservationHistory
    from orthos2.data.models.serialconsole import SerialConsole
    from orthos2.types import (
        MandatoryArchitectureForeignKey,
        MandatoryDomainForeignKey,
        MandatoryEnclosureForeignKey,
        MandatorySystemForeignKey,
        OptionalDateField,
        OptionalDateTimeField,
        OptionalMachineForeignKey,
        OptionalMachineGroupForeignKey,
        OptionalPlatformForeignKey,
        OptionalSmallIntegerField,
        OptionalUserForeignKey,
    )

logger = logging.getLogger("models")
P = ParamSpec("P")
R = TypeVar("R")


def validate_dns(value: str) -> None:
    if not is_dns_resolvable(value):
        raise ValidationError("No DNS lookup result for '{}'".format(value))


def check_permission(
    function: Callable[Concatenate["Machine", P], R],
) -> Callable[Concatenate["Machine", P], R]:
    """Return decorator for checking machine specific methods."""

    def decorator(machine: "Machine", *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Check permission:

        - no `user` keyword                                         -> allow
        - is superuser                                              -> allow
        - is groupadmin (`is_privileged`)                           -> allow
        - machine reserved by user                                  -> allow
        - call `reserve` and not reserved and not administrative    -> allow
        - call `release` and not reserved and not administrative    -> allow

        If no `user` keyword argument is given, access is granted (used for server-side call).
        """
        user = kwargs.get("user", None)

        if not user:
            # grant access if no user is given for e.g. a server call
            return function(machine, *args, **kwargs)

        elif user.is_superuser:  # type: ignore
            logger.debug(
                "Allow %s of %s by %s (superuser)", function.__name__, machine, user
            )
            return function(machine, *args, **kwargs)

        elif user in User.objects.filter(  # type: ignore
            memberships__group__name=machine.group, memberships__is_privileged=True
        ):
            logger.debug(
                "Allow %s of %s by %s (privileged user)",
                function.__name__,
                machine,
                user,
            )
            return function(machine, *args, **kwargs)

        elif machine.reserved_by == user:
            logger.debug(
                "Allow %s of %s by %s (reservation owner)",
                function.__name__,
                machine,
                user,
            )
            return function(machine, *args, **kwargs)

        elif (
            function.__qualname__ == "Machine.reserve"
            and not machine.reserved_by
            and not machine.administrative
        ):
            logger.debug(
                "Allow %s of %s by %s (not reserved)", function.__name__, machine, user
            )
            return function(machine, *args, **kwargs)

        elif (
            function.__qualname__ == "Machine.release"
            and not machine.reserved_by
            and not machine.administrative
        ):
            logger.debug(
                "Allow %s of %s by %s (not reserved)", function.__name__, machine, user
            )
            return function(machine, *args, **kwargs)

        else:
            logger.debug("Deny %s of %s by %s", function.__name__, machine, user)
            raise PermissionDenied("You are not allowed to perform this action!")

    return decorator


class RootManager(models.Manager["Machine"]):
    def get_queryset(self) -> QuerySet["Machine"]:
        """Exclude all inactive machines."""
        queryset = super(RootManager, self).get_queryset()

        return queryset.exclude(active=False)


class ViewManager(RootManager):
    def get_queryset(self, user: Optional[User] = None) -> QuerySet["Machine"]:
        """Exclude administrative machines/systems from all view requested by non-superusers."""
        queryset = super(ViewManager, self).get_queryset()

        if (not user) or (not user.is_superuser):  # type: ignore
            queryset = queryset.exclude(administrative=True)
            queryset = queryset.exclude(system__administrative=True)

        return queryset


class SearchManager(ViewManager):
    def form(
        self, parameters: Dict[str, Any], user: Optional["User"] = None
    ) -> QuerySet["Machine"]:
        """Filter machine queryset by advanced search parameters."""
        parameters = {key: value for key, value in parameters.items() if value}

        queryset = super(SearchManager, self).get_queryset(user=user)
        query = None
        for key, value in parameters.items():
            if not key.endswith("__operator"):
                operator = parameters.get("{}__operator".format(key), "")

                if value == "__True":
                    value = True
                elif value == "__False":
                    value = False

                q = Q(**{"{}{}".format(key, operator): value})
                if query:
                    query = query & q
                else:
                    query = q

        if query:
            queryset = queryset.filter(query).distinct()
        else:
            queryset = queryset.all()

        return queryset


class Machine(models.Model):
    class Manager(models.Manager["Machine"]):
        def get_by_natural_key(self, fqdn: str) -> "Machine":
            return self.get(fqdn=fqdn)

    class Meta:  # type: ignore
        ordering = ["fqdn"]

    class Connectivity:
        NONE = 0
        PING = 1
        SSH = 2
        ALL = 3

    class StatusIP:
        UNREACHABLE = 0
        REACHABLE = 1
        CONFIRMED = 2
        MAC_MISMATCH = 3
        ADDRESS_MISMATCH = 4
        NO_ADDRESS = 5
        AF_DISABLED = 6

        CHOICE = (
            (UNREACHABLE, "unreachable"),
            (REACHABLE, "reachable"),
            (CONFIRMED, "confirmed"),
            (MAC_MISMATCH, "MAC mismatch"),
            (ADDRESS_MISMATCH, "address mismatch"),
            (NO_ADDRESS, "no address assigned"),
            (AF_DISABLED, "address-family disabled"),
        )

    CONNECTIVITY_CHOICE = (
        (Connectivity.NONE, "Disable"),
        (Connectivity.PING, "Ping only"),
        (Connectivity.SSH, "SSH (includes Ping+SSH)"),
        (Connectivity.ALL, "Full (includes Ping+SSH+Login)"),
    )

    # Annotate to allow type checking of autofield
    id: int

    enclosure: "MandatoryEnclosureForeignKey" = models.ForeignKey(
        Enclosure,
        blank=True,
        on_delete=models.CASCADE,
        help_text="Enclosure/chassis of one or more machines",
    )

    fqdn: "models.CharField[str, str]" = models.CharField(
        "FQDN",
        max_length=200,
        blank=False,
        unique=True,
        validators=[validate_domain_ending],
        db_index=True,
        help_text="The Fully Qualified Domain Name of the main network interface of the machine",
    )

    system: "MandatorySystemForeignKey" = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
    )
    system_id: int

    comment: "models.CharField[str, str]" = models.CharField(
        max_length=512,
        blank=True,
        help_text="Machine specific problems or extras you want to tell others?",
    )

    serial_number: "models.CharField[str, str]" = models.CharField(
        max_length=200,
        blank=True,
        help_text="The serial number can be read from a sticker on the machine's chassis (e.g. GPDRDP5022003)",
    )

    product_code: "models.CharField[str, str]" = models.CharField(
        max_length=200,
        blank=True,
        help_text="The product code can be read from a sticker on the machine's chassis (e.g. S1DL1SEXA)",
    )

    architecture: "MandatoryArchitectureForeignKey" = models.ForeignKey(
        Architecture,
        on_delete=models.CASCADE,
    )
    architecture_id: int

    fqdn_domain: "MandatoryDomainForeignKey" = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        help_text="The domain name of the primary NIC",
    )

    cpu_model: "models.CharField[str, str]" = models.CharField(
        "CPU model",
        max_length=200,
        blank=True,
        help_text="The domain name of the primary NIC",
    )

    cpu_flags: "models.TextField[str, str]" = models.TextField(
        "CPU flags",
        blank=True,
        help_text="CPU feature/bug flags as exported from the kernel (/proc/cpuinfo)",
    )

    cpu_physical: "models.IntegerField[int, int]" = models.IntegerField(
        "CPU sockets",
        default=1,
    )

    cpu_cores: "models.IntegerField[int, int]" = models.IntegerField(
        "CPU cores",
        default=1,
        help_text="Amount of CPU cores",
    )

    cpu_threads: "models.IntegerField[int, int]" = models.IntegerField(
        "CPU threads",
        default=1,
        help_text="Amount of CPU threads",
    )

    cpu_speed: "models.DecimalField[Decimal, Decimal]" = models.DecimalField(
        "CPU speed (MHz)",
        default=Decimal(0),
        max_digits=10,
        decimal_places=2,
    )

    cpu_id: "models.CharField[str, str]" = models.CharField(
        "CPU ID",
        max_length=200,
        blank=True,
        help_text="X86 cpuid value which identifies the CPU family/model/stepping and features",
    )

    ram_amount: "models.IntegerField[int, int]" = models.IntegerField(
        "RAM amount (MB)",
        default=0,
    )

    efi: "models.BooleanField[bool, bool]" = models.BooleanField(
        "EFI boot", default=False, help_text="Installed in EFI (aarch64/x86) mode?"
    )

    nda: "models.BooleanField[bool, bool]" = models.BooleanField(
        "NDA hardware",
        default=False,
        help_text="This machine is under NDA and has secret (early development HW?) partner information,"
        " do not share any data to the outside world",
    )

    ipmi: "models.BooleanField[bool, bool]" = models.BooleanField(
        "IPMI capability",
        default=False,
        help_text="IPMI service processor (BMC) detected",
    )

    vm_capable: "models.BooleanField[bool, bool]" = models.BooleanField(
        "VM capable",
        default=False,
        help_text="Do the CPUs support native virtualization (KVM). This field is deprecated",
    )

    vm_max: "models.IntegerField[int, int]" = models.IntegerField(
        "Max. VMs",
        default=6,
        help_text="Maximum amount of virtual hosts allowed to be spawned on this virtual server (ToDo: don't use yet)",
    )

    vm_dedicated_host: "models.BooleanField[bool, bool]" = models.BooleanField(
        "Dedicated VM host",
        default=False,
        help_text="Dedicated to serve as physical host for virtual machines (users cannot reserve this machine)",
    )

    vm_auto_delete: "models.BooleanField[bool, bool]" = models.BooleanField(
        "Delete automatically",
        default=False,
        help_text="Release and destroy virtual machine instances, once people have released"
        "(do not reserve anymore) them",
    )

    virt_api_int: "models.SmallIntegerField[Optional[int], Optional[int]]" = (
        models.SmallIntegerField(
            "Virtualization API",
            choices=VirtualizationAPI.TYPE_CHOICES,
            blank=True,
            null=True,
            help_text="Only supported API currently is libvirt",
        )
    )

    reserved_by: "OptionalUserForeignKey" = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    reserved_at: "OptionalDateTimeField" = models.DateTimeField(blank=True, null=True)

    reserved_until: "OptionalDateTimeField" = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Reservation expires at xx.yy.zzzz (max 90 days)",
    )

    reserved_reason: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        "Reservation reason",
        max_length=512,
        blank=True,
        null=True,
        help_text="Why do you need this machine (bug no, jira feature, what do you test/work on)?",
    )

    platform: "OptionalPlatformForeignKey" = models.ForeignKey(
        Platform, blank=True, null=True, on_delete=models.SET_NULL
    )

    bios_version: "models.CharField[str, str]" = models.CharField(
        max_length=200,
        blank=True,
        help_text="The firmware BIOS is from ... (on x86 as retrieved from dmidecode -s bios-version",
    )

    bios_date: "OptionalDateField" = models.DateField(
        editable=False,
        blank=True,
        null=True,
        default=None,
        help_text="The firmware BIOS is from ... (on x86 as retrieved from dmidecode -s bios-version",
    )

    disk_primary_size: "OptionalSmallIntegerField" = models.SmallIntegerField(
        "Disk primary size (GB)",
        null=True,
        blank=True,
    )

    disk_type: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=True,
    )

    lsmod: "models.TextField[str, str]" = models.TextField(blank=True)

    last: "models.CharField[str, str]" = models.CharField(max_length=100, blank=True)

    hwinfo: "models.TextField[str, str]" = models.TextField(blank=True)

    dmidecode: "models.TextField[str, str]" = models.TextField(blank=True)

    dmesg: "models.TextField[str, str]" = models.TextField(blank=True)

    lsscsi: "models.TextField[str, str]" = models.TextField(blank=True)

    lsusb: "models.TextField[str, str]" = models.TextField(blank=True)

    lspci: "models.TextField[str, str]" = models.TextField(blank=True)

    status_ipv4: "models.SmallIntegerField[int, int]" = models.SmallIntegerField(
        "Status IPv4",
        choices=StatusIP.CHOICE,
        editable=False,
        default=StatusIP.UNREACHABLE,
        help_text="Does this IPv4 address respond to ping?",
    )

    status_ipv6: "models.SmallIntegerField[int, int]" = models.SmallIntegerField(
        "Status IPv6",
        choices=StatusIP.CHOICE,
        editable=False,
        default=StatusIP.UNREACHABLE,
        help_text="Does this IPv6 address respond to ping?",
    )

    status_ssh: "models.BooleanField[bool, bool]" = models.BooleanField(
        "SSH",
        editable=False,
        default=False,
        help_text="Is the ssh port (22) on this host address open?",
    )

    status_login: "models.BooleanField[bool, bool]" = models.BooleanField(
        "Login",
        editable=False,
        default=False,
        help_text="Can orthos log into this host via ssh key (if not scanned data might be outdated)?",
    )

    autoreinstall: "models.BooleanField[bool, bool]" = models.BooleanField(
        "Auto re-install machine",
        editable=True,
        default=True,
        help_text="Shall this machine be automatically re-installed when its reservation ends?<br>"
        "The last installation that has been triggered will be used for auto re-installation.",
    )

    administrative: "models.BooleanField[bool, bool]" = models.BooleanField(
        "Administrative machine",
        editable=True,
        default=False,
        help_text="Administrative machines cannot be reserved",
    )

    check_connectivity: "models.SmallIntegerField[int, int]" = models.SmallIntegerField(
        choices=CONNECTIVITY_CHOICE,
        default=Connectivity.ALL,
        blank=False,
        help_text="Nightly checks whether the machine responds to ping, ssh port is open or whether orthos can"
        "log in via ssh key. Can be triggered manually via command line client: `rescan [fqdn] status`",
    )

    collect_system_information: "models.BooleanField[bool, bool]" = models.BooleanField(
        default=True,
        help_text="Shall the system be scanned every night? This only works if the proper ssh key is in place in"
        " authorized_keys and can be triggered manually via command line client: `rescan [fqdn]`",
    )

    dhcp_filename: "models.CharField[Optional[str], Optional[str]]" = models.CharField(
        "DHCP filename",
        max_length=64,
        null=True,
        blank=True,
        help_text="Override bootloader binary retrieved from a tftp server (corresponds to the `filename`"
        " ISC dhcpd.conf variable)",
    )

    tftp_server: "OptionalMachineForeignKey" = models.ForeignKey(
        "data.Machine",
        related_name="tftp_server_for",
        verbose_name="TFTP server",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"administrative": True},
        help_text="Override tftp server used for network boot (corresponds to the `next_server` ISC"
        " dhcpd.conf variable)",
    )

    hypervisor: "OptionalMachineForeignKey" = models.ForeignKey(
        "data.Machine",
        related_name="hypervising",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The physical host this virtual machine is running on",
    )

    active: "models.BooleanField[bool, bool]" = models.BooleanField(
        default=True,
        help_text="Machine vanishes from most lists. This is intendend as kind of maintenance/repair state",
    )

    group: "OptionalMachineGroupForeignKey" = models.ForeignKey(
        MachineGroup, on_delete=models.SET_NULL, blank=True, null=True
    )

    contact_email: "models.EmailField[str, str]" = models.EmailField(
        blank=True,
        help_text="Override contact email address to whom is in charge for this machine",
    )

    kernel_options: "models.CharField[str, str]" = models.CharField(
        max_length=4096,
        blank=True,
        help_text="Additional kernel command line parameters to pass",
    )

    last_check: "models.DateTimeField[datetime.datetime, datetime.datetime]" = (
        models.DateTimeField(
            "Checked at",
            editable=False,
            default=datetime.datetime(
                year=2016,
                month=1,
                day=1,
                hour=10,
                minute=0,
                second=00,
                tzinfo=datetime.timezone.utc,
            ),
        )
    )

    netbox_id: "models.PositiveIntegerField[int, int]" = models.PositiveIntegerField(
        verbose_name="NetBox ID",
        help_text="The ID that NetBox gives to the object.",
        default=0,
    )

    updated: "models.DateTimeField[datetime.datetime, datetime.datetime]" = (
        models.DateTimeField("Updated at", auto_now=True)
    )

    created: "models.DateTimeField[datetime.datetime, datetime.datetime]" = (
        models.DateTimeField("Created at", auto_now_add=True)
    )

    networkinterfaces: "RelatedManager[NetworkInterface]"
    domain_set: "Domain"
    cobbler_server_for: "RelatedManager[Machine]"
    cscreen_server_for: "RelatedManager[Machine]"
    tftp_server_for_domain: "Domain"
    hypervising: "RelatedManager[Machine]"
    remotepower: "RemotePower"
    bmc: "BMC"
    installations: "Installation"
    serialconsole: "SerialConsole"
    annotations: "RelatedManager[Annotation]"
    reservationhistory_set: "RelatedManager[ReservationHistory]"

    objects = Manager()
    api = RootManager()
    active_machines = RootManager()
    search = SearchManager()
    view = ViewManager()

    def natural_key(self) -> Tuple[str]:
        return (self.fqdn,)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Deep copy object for comparison in `save()`."""
        super(Machine, self).__init__(*args, **kwargs)

        if self.pk is not None:
            self._original = deepcopy(self)
        else:
            self._original = None

        # Only use machine.unsaved_networkinterfaces in the context of VMs
        self.unsaved_networkinterfaces: "List[NetworkInterface]" = []
        # Only use machine.vnc in the context of VMs
        self.vnc: Dict[str, Any] = {}
        self.virtualization_api = virtualization_api_factory(self.virt_api_int, self)

    def __str__(self) -> str:
        return self.fqdn

    @property
    def ip_address_v4(self) -> Optional[str]:
        intf = self.get_primary_networkinterface()
        if intf is None:
            return None
        return intf.ip_address_v4

    @property
    def ip_address_v6(self) -> Optional[str]:
        intf = self.get_primary_networkinterface()
        if intf is None:
            return None
        return intf.ip_address_v6

    @property
    def hostname(self) -> str:
        return get_hostname(self.fqdn)

    @property
    def mac_address(self) -> Optional[str]:
        intf = self.get_primary_networkinterface()
        if intf is None:
            return None
        return intf.mac_address

    def fetch_netbox(self) -> None:
        """
        Fetch information from Netbox.
        """
        if self.netbox_id == 0:
            logger.debug("Skipping fetching from NetBox because NetBox ID is 0.")
            return
        netbox_api = Netbox.get_instance()
        try:
            netbox_machine = netbox_api.fetch_device(self.netbox_id)
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.info("Fetching from NetBox failed with status 404.")
                return
            raise e
        # Reset fields
        self.comment = ""
        self.serial_number = ""
        self.product_code = ""
        # Description
        self.comment = netbox_machine.get("description", "")
        # Serial Number
        self.serial_number = netbox_machine.get("serial", "")
        # Product Code
        product_code = netbox_machine.get("custom_fields", {}).get("product_code", "")
        if product_code is not None and product_code != "":
            self.product_code = product_code
        # Verify all NetworkInterfaces are created
        device_network_interfaces = netbox_api.check_interface_no_mgmt_by_id(
            self.netbox_id
        )
        synced_mac_addresses: Set[str] = set()
        for interface in device_network_interfaces:
            primary_mac = interface.get("primary_mac_address")
            if primary_mac is None:
                continue
            # If interface exists with MAC, then sync
            if primary_mac.get("mac_address") in synced_mac_addresses:
                # This is most probably a bonded interface, and we synchronize the first interface.
                continue
            synced_mac_addresses.add(primary_mac.get("mac_address"))
            ipv4_addresses = netbox_api.check_ip_by_interface_family(
                interface.get("id"), 4  # type: ignore
            )
            ipv6_addresses = netbox_api.check_ip_by_interface_family(
                interface.get("id"), 6  # type: ignore
            )
            if len(ipv4_addresses) > 1 or len(ipv6_addresses) > 1:
                # TODO: Handle case
                continue
            try:
                # Use existing interface if possible
                orthos_network_interface = NetworkInterface.objects.get(
                    mac_address=primary_mac.get("mac_address")
                )
                if orthos_network_interface.machine.id != self.id:
                    # If on different machine --> Remove from machine and assign to this machine
                    orthos_network_interface.machine_id = self.id
            except ObjectDoesNotExist:
                # Create Network Interface if not mgmt interface
                orthos_network_interface = NetworkInterface()
                orthos_network_interface.mac_address = primary_mac.get("mac_address")
                orthos_network_interface.machine_id = self.id
            # Update interface information
            orthos_network_interface.ethernet_type = interface.get("type").get("label")  # type: ignore
            orthos_network_interface.name = interface.get("name")  # type: ignore
            if len(ipv4_addresses) > 0:
                orthos_network_interface.ip_address_v4 = str(
                    ipaddress.ip_network(
                        ipv4_addresses[0].get("address")  # type: ignore
                    ).network_address
                )
            if len(ipv6_addresses) > 0:
                orthos_network_interface.ip_address_v6 = str(
                    ipaddress.ip_network(
                        ipv6_addresses[0].get("address")  # type: ignore
                    ).network_address
                )
            orthos_network_interface.save()
        mgmt_interfaces = netbox_api.check_interface_mgmt_by_id(self.netbox_id)
        if len(mgmt_interfaces) > 1:
            # Skip multi-mgmt interfaces for now. Feature will be implemented later.
            logger.warning(
                "Skipping fetching BMC data from NetBox since there is more then a single network interface."
            )
        for mgmt_interface in mgmt_interfaces:
            primary_mac = mgmt_interface.get("primary_mac_address")
            # Don't attempt to do things without a MAC address
            if primary_mac is None:
                continue
            ipv4_addresses = netbox_api.check_ip_by_interface_family(
                mgmt_interface.get("id"), 4  # type: ignore
            )
            ipv6_addresses = netbox_api.check_ip_by_interface_family(
                mgmt_interface.get("id"), 6  # type: ignore
            )
            if len(ipv4_addresses) > 1 or len(ipv6_addresses) > 1:
                # TODO: Handle case
                continue
            if ipv4_addresses[0].get("dns_name") != ipv6_addresses[0].get("dns_name"):
                logger.warning(
                    "Skipped updating BMC interface because IPv4 and IPv6 DNS name are different!"
                )
                continue
            fence_name = mgmt_interface.get("custom_fields", {}).get("fence_agent", "")
            if fence_name == "":
                logger.warning("Skipped because BMC interface has no fence name set!")
                continue
            if self.has_bmc():
                bmc = BMC.objects.get(mac=primary_mac.get("mac_address"))
                if bmc.machine_id != self.id:
                    logger.warning(
                        'BMC interface with MAC "%s" wasn\'t assigned to current machine %s but to machine %s!',
                        primary_mac.get("mac_address"),
                        self.id,
                        bmc.machine_id,
                    )
                    continue
            else:
                bmc = BMC()
                bmc.machine_id = self.id
            bmc.fqdn = ipv4_addresses[0].get("dns_name")  # type: ignore
            bmc.fence_agent = RemotePowerType.objects.get(name=fence_name)
            bmc.mac = primary_mac.get("mac_address")
            if len(ipv4_addresses) > 0:
                bmc.ip_address_v4 = str(
                    ipaddress.ip_network(
                        ipv4_addresses[0].get("address")  # type: ignore
                    ).network_address
                )
            if len(ipv6_addresses) > 0:
                bmc.ip_address_v6 = str(
                    ipaddress.ip_network(
                        ipv6_addresses[0].get("address")  # type: ignore
                    ).network_address
                )
            # Username & Password will be pulled from Hashicorp Vault in the future but for
            # now they have to be manually given.
            bmc.save()
        self.save()

    def bmc_allowed(self) -> bool:
        return self.system.allowBMC

    def has_bmc(self) -> bool:
        return hasattr(self, "bmc")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save machine object.

        Set FQDN to lower case, check if FQDN is resolvable by DNS and set
        domain and enclosure correctly (create if necessary).
        """
        self.fqdn = self.fqdn.lower()

        validate_domain_ending(self.fqdn)

        if self.pk is not None and self.mac_address:
            validate_mac_address(self.mac_address)

        if not self.system.virtual and self.hypervisor:
            raise ValidationError("Only virtual machines may have hypervisors")
        if hasattr(self, "bmc") and not self.bmc_allowed():
            raise ValidationError(
                "{} systems cannot use a BMC".format(self.system.name)
            )
        self.fqdn_domain = Domain.objects.get(name=get_domain(self.fqdn))

        # create & assign enclosure according to naming convention if no enclosure given
        if not hasattr(self, "enclosure"):
            name = re.split(r"-(\d|sp)+$", get_hostname(self.fqdn))[0]
            enclosure, _ = Enclosure.objects.get_or_create(name=name)
            self.enclosure = enclosure

        super(Machine, self).save(*args, **kwargs)
        sync_dhcp = False
        update_machine = False
        update_sconsole = False
        if self._original is None:
            try:
                NetworkInterface.objects.get(machine=self, primary=True)
            except ObjectDoesNotExist:
                if self.mac_address:
                    self.networkinterfaces.get_or_create(
                        machine=self, primary=True, mac_address=self.mac_address
                    )
                    sync_dhcp = True
                    update_machine = True
        else:
            # check if DHCP needs to be regenerated
            if self.mac_address != self._original.mac_address:
                self.delete_secondary_interfaces()
            if any(
                [
                    self.mac_address != self._original.mac_address,
                    self.fqdn != self._original.fqdn,
                    self.fqdn_domain != self._original.fqdn_domain,
                    self.architecture != self._original.architecture,
                    self.group != self._original.group,
                    self.dhcp_filename != self._original.dhcp_filename,
                    self.kernel_options != self._original.kernel_options,
                ]
            ):
                sync_dhcp = True
                update_machine = True
            if self.has_bmc():
                if not hasattr(self._original, "bmc"):
                    # BMC added
                    sync_dhcp = True
                    update_machine = True
                    update_sconsole = True
                if hasattr(self._original, "bmc") and any(
                    [
                        self.bmc.mac != self._original.bmc.mac,
                        self.bmc.fqdn != self._original.bmc.fqdn,
                        self.bmc.username != self._original.bmc.username,
                        self.bmc.password != self._original.bmc.password,
                    ]
                ):
                    # BMC updated
                    sync_dhcp = True
                    update_machine = True
                    update_sconsole = True
            if self.has_remotepower():
                if not hasattr(self._original, "remotepower") or not hasattr(
                    self._original, "remote_power_device"
                ):
                    # Remotepower or remote power device added
                    update_machine = True
                if hasattr(self._original, "remotepower") and any(
                    [
                        self.remotepower.fence_agent
                        != self._original.remotepower.fence_agent,
                        self.remotepower.options != self._original.remotepower.options,
                    ]
                ):
                    # Remotepower updated
                    update_machine = True
                if (
                    hasattr(self.remotepower, "remote_power_device")
                    and self._original.has_remotepower()
                    and any(
                        [
                            not hasattr(
                                self._original.remotepower, "remote_power_device"
                            ),
                            self.remotepower.remote_power_device
                            != self._original.remotepower.remote_power_device,
                        ]
                    )
                ):
                    # Remote power device updated
                    update_machine = True
            if self.has_serialconsole():
                if not hasattr(self._original, "serialconsole"):
                    # Serial console added
                    update_sconsole = True
                    update_machine = True
                if hasattr(self._original, "serialconsole") and any(
                    [
                        self.serialconsole.baud_rate
                        != self._original.serialconsole.baud_rate,
                        self.serialconsole.command
                        != self._original.serialconsole.command,
                        self.serialconsole.stype == self._original.serialconsole.stype,
                        self.serialconsole.kernel_device
                        != self._original.serialconsole.kernel_device,
                        self.serialconsole.kernel_device_num
                        != self._original.serialconsole.kernel_device_num,
                    ]
                ):
                    # Serial console updated
                    update_sconsole = True
                    update_machine = True

            if self.fqdn_domain != self._original.fqdn_domain:
                logger.info(f"Domain change for: %s", self.fqdn)
                # TODO: add error handling (checking whether the signal went through)
                # Not removing the machine from the original Cobbler system, because there is no easy remove signal
                # and it's probably not even necessary
                # Add the machine to the new Cobbler system
                # TODO: check if machine is known to us, and also a cobbler server
                new_domain_id = self.fqdn_domain.pk
                from orthos2.data.signals import signal_cobbler_machine_update

                signal_cobbler_machine_update.send(  # type: ignore
                    sender=self.__class__, machine_id=self.pk, domain_id=new_domain_id
                )

                # Sync DHCP on the new domain
                from orthos2.data.signals import signal_cobbler_sync_dhcp

                signal_cobbler_sync_dhcp.send(  # type: ignore
                    sender=self.__class__, domain_id=new_domain_id
                )
                return

        if update_machine:
            from orthos2.data.signals import signal_cobbler_machine_update

            logger.debug("Update machine initiated [%s]", self.fqdn)
            domain_id = self.fqdn_domain.pk
            machine_id = self.pk
            signal_cobbler_machine_update.send(  # type: ignore
                sender=self.__class__, domain_id=domain_id, machine_id=machine_id
            )
        if sync_dhcp:
            from orthos2.data.signals import signal_cobbler_sync_dhcp

            # regenerate DHCP on all domains (deletion/registration) if domain changed
            domain_id = self.fqdn_domain.pk
            signal_cobbler_sync_dhcp.send(  # type: ignore
                sender=self.__class__,
                domain_id=domain_id,
            )
            self.scan("networkinterfaces")
        if update_sconsole:
            from orthos2.data.signals import signal_serialconsole_regenerate

            if (
                hasattr(self.fqdn_domain, "cscreen_server")
                and self.fqdn_domain.cscreen_server is not None
            ):
                cscreen_server_fqdn = self.fqdn_domain.cscreen_server.fqdn
                signal_serialconsole_regenerate.send(  # type: ignore
                    sender=self.__class__, cscreen_server_fqdn=cscreen_server_fqdn
                )

    @property
    def status_ping(self) -> bool:
        return self.status_ipv4 in {
            Machine.StatusIP.REACHABLE,
            Machine.StatusIP.CONFIRMED,
        } or self.status_ipv6 in {
            Machine.StatusIP.REACHABLE,
            Machine.StatusIP.CONFIRMED,
        }

    def is_reserved(self) -> bool:
        if self.reserved_by:
            return True
        return False

    is_reserved.boolean = True  # type: ignore

    def is_administrative(self) -> bool:
        return self.administrative

    is_administrative.boolean = True  # type: ignore

    def is_cobbler_server(self) -> bool:
        return self.cobbler_server_for.exists()  # type: ignore

    def is_cscreen_server(self) -> bool:
        return self.cscreen_server_for.exists()  # type: ignore

    is_cobbler_server.boolean = True  # type: ignore

    def is_virtual_machine(self) -> bool:
        """
        Is this a virtualized system?

        "return: `True` if machine is a virtual machine (system)
        """
        return self.system.virtual

    def is_vm_managed(self) -> bool:
        """
        Is this a virtual machine and has a hypervisor and virt API assigned
        through which it is managed?

        :return: `True` if machine has a hypervisor and a virtualization API assgined.
        """
        return (
            self.hypervisor is not None
            and self.hypervisor.virtualization_api is not None
        )

    def get_cobbler_domains(self) -> Optional[QuerySet["Domain"]]:
        if not self.is_cobbler_server():
            return None
        return self.domain_set.all()  # type: ignore

    def get_active_distribution(self) -> Optional["Installation"]:
        return self.installations.get(active=True)  # type: ignore

    def delete_secondary_interfaces(self) -> None:
        primary = self.get_primary_networkinterface()
        for network in self.networkinterfaces.all():  # type: ignore
            if network != primary:
                network.delete()

    def get_primary_networkinterface(self) -> Optional[NetworkInterface]:
        try:
            interface = self.networkinterfaces.get(primary=True)  # type: ignore
        except NetworkInterface.DoesNotExist:
            logger.debug(
                "In 'get_primary_networkinterface': Machine %s has no networkinterfce",
                self.fqdn,
            )
            return None
        return interface

    def get_virtual_machines(self) -> Optional[QuerySet["Machine"]]:
        if not self.is_virtual_machine():
            return self.hypervising.all()
        return None

    def get_kernel_options(self) -> Dict[str, Optional[str]]:
        """Return kernel options as dict."""
        kernel_options: Dict[str, Optional[str]] = {}

        if not self.kernel_options.strip().startswith("+"):
            for kernel_option in self.kernel_options.strip().split():
                option = kernel_option.split("=")
                key = option[0]
                value = option[1] if len(option) == 2 else None
                kernel_options[key] = value

        return kernel_options

    def get_kernel_options_append(self) -> Dict[str, Optional[str]]:
        """Return kernel options append as dict."""
        kernel_options: Dict[str, Optional[str]] = {}

        if self.kernel_options.strip().startswith("+"):
            for kernel_option in self.kernel_options.strip()[1:].split():
                option = kernel_option.split("=")
                key = option[0]
                value = option[1] if len(option) == 2 else None
                kernel_options[key] = value

        return kernel_options

    def get_s390_hostname(self, use_uppercase: bool = False) -> Optional[str]:
        if self.system.name == "zVM":
            return get_s390_hostname(self.hostname, use_uppercase=use_uppercase)  # type: ignore
        return None

    def has_remotepower(self) -> bool:
        """Check for available remote power."""
        return hasattr(self, "remotepower")

    def has_serialconsole(self) -> bool:
        """Check for available serial console."""
        return hasattr(self, "serialconsole")

    def is_reserved_infinite(self) -> bool:
        """Return true if machine is reserved infinite `datetime.date(9999, 12, 31)`."""
        if self.reserved_by and self.reserved_until.date() == datetime.date.max:  # type: ignore
            return True
        return False

    def has_setup_capability(self) -> bool:
        """
        Return true if a machines network domain supports the setup capability for the respective
        machine group (if the machine belongs to one) or architecture.
        """
        return self.architecture in self.fqdn_domain.supported_architectures.all()

    @check_permission
    def reserve(
        self,
        reason: str,
        until: datetime.date,
        user: Optional["User"] = None,
        reserve_for_user: Optional["User"] = None,
    ) -> None:
        """Reserve machine."""
        from .reservationhistory import ReservationHistory

        from orthos2.taskmanager import tasks
        from orthos2.taskmanager.models import TaskManager

        if not reserve_for_user:
            reserve_for_user = user

        extension = True

        if not reason:
            raise ReserveException("Please provide a reservation reason.")

        if until == datetime.date.max and not user.is_superuser:  # type: ignore
            raise ReserveException("Infinite reservation is not allowed.")

        # add to history if a superuser takes over the reservation
        if self.reserved_by and (self.reserved_by not in {user, reserve_for_user}):
            reservationhistory = ReservationHistory(  # type: ignore
                machine=self,
                reserved_by=self.reserved_by,
                reserved_at=self.reserved_at,
                reserved_until=timezone.now(),
                reserved_reason="{} (taken away by {})".format(
                    self.reserved_reason, user
                ),
            )
            reservationhistory.save()
            self.reserved_at = None

        self.reserved_by = reserve_for_user
        self.reserved_reason = reason
        if not self.reserved_at:
            self.reserved_at = timezone.now()
            extension = False

        # Infinte reservation:
        # --------------------
        # Use `datetime.date.max` for the date and `datetime.time.min` for the time.
        # The minimum time (0, 0) must be set so that the correct time zone calculation does not
        # exceed the maximum DateTime limit (CET (UTC+1) of 9999-12-31, 23:59 (UTC) would result
        # in `OverflowError: date value out of range`).

        # Normal reservation (not infinite):
        # ----------------------------------
        # Combine the `datetime.date` object with `datetime.time.max` (23, 59) and make the
        # new `datetime.datetime` object time zone aware using the default time zone (see
        # `TIME_ZONE` in the django settings).
        if until == datetime.date.max:
            until = timezone.datetime.combine(  # type: ignore
                datetime.date.max, timezone.datetime.min.time()  # type: ignore
            )
            until = timezone.make_aware(until, timezone.utc)  # type: ignore
        else:
            until = timezone.datetime.combine(until, timezone.datetime.max.time())  # type: ignore
            until = timezone.make_aware(until, timezone.get_default_timezone())  # type: ignore

        self.reserved_until = until
        self.save()

        self.update_motd()

        if not extension:
            task = tasks.SendReservationInformation(reserve_for_user.id, self.fqdn)  # type: ignore
            TaskManager.add(task)

    @check_permission
    def release(self, user: Any = None) -> None:
        """Release machine."""
        from .reservationhistory import ReservationHistory

        if not self.is_reserved():
            raise ReleaseException("Machine is not reserved.")

        if self.administrative:
            raise Exception(
                "Administrative machines must not be released, remove admin flag first"
            )

        logger.debug("Release VM %s", self.fqdn)
        if self.is_vm_managed() and self.hypervisor.vm_auto_delete:  # type: ignore
            logger.debug("Delete VM %s", self.fqdn)
            self.delete()
            return

        reservationhistory = ReservationHistory(  # type: ignore
            machine=self,
            reserved_by=self.reserved_by,
            reserved_at=self.reserved_at,
            reserved_until=timezone.now(),
            reserved_reason=self.reserved_reason,
        )

        self.reserved_by = None
        self.reserved_reason = None
        self.reserved_at = None
        self.reserved_until = None

        self.save()
        reservationhistory.save()

        if self.autoreinstall:
            self.setup(self.architecture.default_profile)
        else:
            self.update_motd()

    @check_permission
    def powercycle(self, action: Optional[str], user: Any = None) -> bool:
        """Act as proxy for all power cycle actions."""
        from .remotepower import RemotePower

        if (action is None) or (action not in RemotePower.Action.as_list):
            raise Exception(
                "Power cycling failed: unknown action ('{}')!".format(action)
            )

        if not self.has_remotepower():
            raise Exception("No remotepower available!")

        if action == RemotePower.Action.STATUS:
            return self.get_power_status()  # type: ignore

        elif action == RemotePower.Action.ON:
            return self.power_on()

        elif action == RemotePower.Action.OFF:
            return self.power_off()

        elif action == RemotePower.Action.REBOOT:
            return self.reboot()

        elif action == RemotePower.Action.OFF_SSH:
            return self.power_off_ssh()

        elif action == RemotePower.Action.OFF_REMOTEPOWER:
            return self.power_off_remotepower()

        elif action == RemotePower.Action.REBOOT_SSH:
            return self.reboot_ssh()

        elif action == RemotePower.Action.REBOOT_REMOTEPOWER:
            if self.has_remotepower():
                return self.reboot_remotepower()

        return False

    @check_permission
    def ssh_shutdown(self, user: Any = None, reboot: bool = False) -> bool:
        """Power off/reboot the machine using SSH."""
        from orthos2.utils.ssh import SSH

        if reboot:
            option = "--reboot"
        else:
            option = "--poweroff"

        machine = SSH(self.fqdn)
        machine.connect()
        command = "shutdown {} now".format(option)
        _stdout, _stderr, exitstatus = machine.execute(command, retry=False)
        machine.close()

        if exitstatus != 0:
            return False

        return True

    @check_permission
    def setup(self, setup_label: Optional[str] = None, user: Any = None) -> bool:
        """Setup machine (re-install distribution)."""
        from orthos2.taskmanager import tasks
        from orthos2.taskmanager.models import TaskManager

        if self.has_setup_capability():
            task = tasks.SetupMachine(self.fqdn, setup_label)
            TaskManager.add(task)
            return True

        return False

    @check_permission
    def power_on(self, user: Any = None) -> bool:
        """Power on the machine."""
        self.remotepower.power_on()
        return True

    @check_permission
    def power_off(self, user: Any = None) -> bool:
        """
        Power off the machine.

        Try power off via SSH first. If SSH didn't succeed, trigger power off via remote power if
        available.
        """
        from orthos2.utils.ssh import SSH

        result = False

        try:
            result = self.ssh_shutdown()
        except SSH.Exception:
            pass

        if not result and self.has_remotepower():
            return self.power_off_remotepower(user=user)
        return True

    @check_permission
    def power_off_ssh(self, user: Any = None) -> bool:
        """Power off the machine using SSH. Wrapper for `ssh_shutdown()`."""
        return self.ssh_shutdown()

    @check_permission
    def power_off_remotepower(self, user: Any = None) -> bool:
        """Power off the machine via remote power."""
        self.remotepower.power_off()
        return True

    @check_permission
    def reboot(self, user: Any = None) -> bool:
        """
        Power off the machine.

        Try power off via SSH first. If SSH didn't succeed, trigger power off via remote power if
        available.
        """
        from orthos2.utils.ssh import SSH

        result = False

        try:
            result = self.ssh_shutdown(reboot=True)
        except SSH.Exception:
            pass

        if not result and self.has_remotepower():
            return self.reboot_remotepower(user=user)
        return True

    @check_permission
    def reboot_ssh(self, user: Any = None) -> bool:
        """Reboot the machine using SSH. Wrapper for `ssh_shutdown(reboot=True)`."""
        return self.ssh_shutdown(reboot=True)

    @check_permission
    def reboot_remotepower(self, user: Any = None) -> bool:
        """Reboot the machine via remote power."""
        if self.has_remotepower():
            self.remotepower.reboot()
        return True

    def get_power_status(self, to_str: bool = True) -> Union[str, int]:
        """Return the current power status."""
        from .remotepower import RemotePower

        if not self.has_remotepower():
            return RemotePower.Status.UNKNOWN

        status = self.remotepower.get_status()
        if to_str:
            return RemotePower.Status.to_str(status)
        return status

    def scan(self, action: str = "all", user: Any = None) -> None:
        """Start scanning/checking the machine by creating a task."""
        from orthos2.taskmanager import tasks
        from orthos2.taskmanager.models import TaskManager
        from orthos2.taskmanager.tasks.ansible import Ansible

        if action.lower() not in tasks.MachineCheck.Scan.Action.as_list:
            raise Exception("Unknown scan option '{}'!".format(action))

        task = tasks.MachineCheck(self.fqdn, tasks.MachineCheck.Scan.to_int(action))
        TaskManager.add(task)

        # ToDo: Better wait until individual machine scans finished
        if action == "all":
            TaskManager.add(Ansible([self.fqdn]))

    @check_permission
    def update_motd(self, user: Any = None) -> None:
        """Call respective signal."""
        from orthos2.data.signals import signal_motd_regenerate

        signal_motd_regenerate.send(sender=self.__class__, fqdn=self.fqdn)  # type: ignore

    @check_permission
    def regenerate_serialconsole_record(self, user: Any = None) -> None:
        """Call respective signal."""
        from orthos2.data.signals import signal_serialconsole_regenerate

        if self.has_serialconsole():
            signal_serialconsole_regenerate.send(  # type: ignore
                sender=self.__class__,
                cscreen_server_fqdn=self.fqdn_domain.cscreen_server.fqdn,  # type: ignore
            )

    @check_permission
    def regenerate_dhcp_record(self, user: Any = None) -> None:
        """Call respective signal."""
        from orthos2.data.signals import signal_cobbler_regenerate

        signal_cobbler_regenerate.send(  # type: ignore
            sender=self.__class__, domain_id=self.fqdn_domain.pk
        )

    def get_support_contact(self) -> str:
        """
        Return email address for responsible support contact (default: SUPPORT_CONTACT).

        Machine > [Group >] Architecture > SUPPORT_CONTACT
        """
        if self.contact_email:
            return self.contact_email

        if self.group:
            contact = self.group.get_support_contact()
            if contact:
                return contact

        admin = DomainAdmin.objects.get(domain=self.fqdn_domain, arch=self.architecture)
        if admin and admin.contact_email:
            return admin.contact_email

        return settings.SUPPORT_CONTACT

    def serialize(self, output_format: str) -> Tuple[str, str]:
        """
        Serialize machine with its relations.

        Valid output formats are JSON and Yaml.
        """
        output_format = output_format.lower()

        if not Serializer.Format.is_valid(output_format):
            logger.warning("Unknown serialize format! Continues with JSON...")
            output_format = Serializer.Format.JSON

        querysets = [
            [self],
            self.networkinterfaces.all(),
            [self.remotepower] if self.has_remotepower() else None,
            [self.serialconsole] if self.has_serialconsole() else None,
            self.annotations.all(),
            self.reservationhistory_set.all(),
        ]

        serializer = serializers.get_serializer(output_format)()
        chunks: List[str] = []

        for _i, queryset in enumerate(querysets):

            if queryset is None:
                continue

            chunks.append(
                serializer.serialize(
                    queryset,
                    indent=4,
                    use_natural_foreign_keys=True,
                    use_natural_primary_keys=True,
                )
            )

        data = "\n".join(chunks)

        return (data, output_format)
