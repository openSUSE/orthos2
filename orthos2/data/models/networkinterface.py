import ipaddress
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Iterable, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import models
from requests import HTTPError

from orthos2.data.models.netboxorthoscomparision import (
    NetboxOrthosComparisionResult,
    NetboxOrthosComparisionRun,
)
from orthos2.data.validators import validate_mac_address
from orthos2.utils import misc
from orthos2.utils.netbox import Netbox

if TYPE_CHECKING:
    from orthos2.types import MandatoryMachineForeignKey

logger = logging.getLogger("models")


class NetworkInterface(models.Model):
    class Meta:  # type: ignore
        verbose_name = "Network Interface"
        ordering = ("-primary",)

    machine_id: int
    machine: "MandatoryMachineForeignKey" = models.ForeignKey(
        "data.Machine",
        related_name="networkinterfaces",
        editable=False,
        on_delete=models.CASCADE,
    )

    primary: "models.BooleanField[bool, bool]" = models.BooleanField(
        "Primary",
        blank=False,
        default=False,
    )

    mac_address: "models.CharField[str, str]" = models.CharField(
        "MAC address",
        max_length=20,
        blank=False,
        unique=True,
        validators=[validate_mac_address],
    )

    ip_address_v4: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv4",
            unique=True,
            null=True,
            blank=True,
            verbose_name="IPv4 address",
            help_text="IPv4 address",
        )
    )

    ip_address_v6: "models.GenericIPAddressField[Optional[str], Optional[str]]" = (
        models.GenericIPAddressField(
            protocol="IPv6",
            unique=True,
            null=True,
            blank=True,
            verbose_name="IPv6 address",
            help_text="IPv6 address",
        )
    )

    ethernet_type: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=True,
    )

    driver_module: "models.CharField[str, str]" = models.CharField(
        max_length=100,
        blank=True,
    )

    name: "models.CharField[str, str]" = models.CharField(
        max_length=20,
        blank=False,
        default="unknown",
    )

    updated: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        "Updated at",
        auto_now=True,
    )

    created: "models.DateTimeField[datetime, datetime]" = models.DateTimeField(
        "Created at",
        auto_now_add=True,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # The two attributes below are only used for network interfaces that are attached to a VM.
        self.model = ""
        self.bridge = ""

    def natural_key(self) -> Tuple[str]:
        return (self.mac_address,)

    def __str__(self) -> str:
        if self.primary:
            return "{} ({}/{})".format(self.mac_address, self.name, "primary")
        return "{} ({})".format(self.mac_address, self.name)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.clean()
        return super(NetworkInterface, self).save(*args, **kwargs)

    def clean(self) -> None:
        """Validate, convert to upper case and check if MAC address already exists."""
        self.mac_address = self.mac_address.upper()
        validate_mac_address(self.mac_address)

        exclude: Iterable[str] = []
        if hasattr(self, "machine"):
            exclude = self.machine.networkinterfaces.all().values_list(
                "mac_address", flat=True
            )

        if not misc.is_unique_mac_address(self.mac_address, exclude=exclude):
            violate_net = NetworkInterface.objects.get(mac_address=self.mac_address)
            if hasattr(violate_net, "machine"):
                violate_machine = violate_net.machine.fqdn
            else:
                violate_machine = "networkinterface not assigned to a machine"
            raise ValidationError(
                "MAC address '{}' is already in use by: {}".format(
                    self.mac_address, violate_machine
                )
            )

    def compare_netbox(self) -> None:
        """
        Compare the current data in the database of Orthos 2 with the data from NetBox.
        """
        if self.machine.netbox_id == 0:
            logger.debug("Skipping comparision because NetBox ID is 0.")
            return

        run_uuid = uuid.uuid4()
        run_obj = NetboxOrthosComparisionRun(
            run_id=run_uuid,
            compare_timestamp=datetime.now(),
            object_type=NetboxOrthosComparisionRun.NetboxOrthosComparisionItemTypes.NETWORK_INTERFACE,
            object_network_interface=self,
        )
        run_obj.save()

        netbox_api = Netbox.get_instance()
        try:
            netbox_machine = netbox_api.fetch_device(self.machine.netbox_id)
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.info("Fetching from NetBox failed with status 404.")
                return
            raise e
        netbox_interfaces = netbox_api.check_interface_no_mgmt_by_id(
            self.machine.netbox_id
        )
        netbox_target_interface = {}
        for interface in netbox_interfaces:
            if interface.get("primary_mac_address") is None:
                continue
            if (
                interface.get("primary_mac_address", {}).get("display", "")
                == self.mac_address
            ):
                netbox_target_interface = interface
                break

        # Name
        NetboxOrthosComparisionResult(
            run_id=run_obj,
            property_name="name",
            orthos_result=self.name or "None",
            netbox_result=netbox_target_interface.get("display", "None"),
        ).save()

        ips = netbox_api.check_ip_by_interface(netbox_target_interface.get("id"))  # type: ignore
        if len(ips) == 0:
            logger.debug("No IPs assigned to this interface.")
            return
        if len(ips) > 2:
            logger.warning("Too many IPs assigned to this interface.")
            return

        machine_primary_ipv4 = netbox_machine.get("primary_ip4")
        machine_primary_ipv6 = netbox_machine.get("primary_ip6")
        for ip in ips:
            ip_obj = ipaddress.ip_network(ip.get("display"))  # type: ignore
            # IPv4 Address
            if ip_obj.version == 4:
                NetboxOrthosComparisionResult(
                    run_id=run_obj,
                    property_name="ip_address_v4",
                    orthos_result=self.ip_address_v4 or "None",
                    netbox_result=str(ip_obj),
                ).save()
            # IPv6 Address
            if ip_obj.version == 6:
                NetboxOrthosComparisionResult(
                    run_id=run_obj,
                    property_name="ip_address_v6",
                    orthos_result=self.ip_address_v6 or "None",
                    netbox_result=str(ip_obj),
                ).save()
            if machine_primary_ipv4 is not None and machine_primary_ipv4.get(
                "id", 0
            ) == ip.get("id", -1):
                self.primary = True
            if machine_primary_ipv6 is not None and machine_primary_ipv6.get(
                "id", 0
            ) == ip.get("id", -1):
                self.primary = True

        # Machine
        # Primary
        # MAC Address
        # Ethernet Type
        # DNS Name

    def fetch_netbox(self) -> None:
        """
        Fetch information from Netbox.
        """
        if self.machine.netbox_id == 0:
            logger.debug("Skipping fetching from NetBox because NetBox ID is 0.")
            return
        netbox_api = Netbox.get_instance()
        try:
            netbox_machine = netbox_api.fetch_device(self.machine.netbox_id)
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.info("Fetching from NetBox failed with status 404.")
                return
            raise e
        netbox_interfaces = netbox_api.check_interface_no_mgmt_by_id(
            self.machine.netbox_id
        )
        netbox_target_interface = {}
        for interface in netbox_interfaces:
            if interface.get("primary_mac_address") is None:
                continue
            if (
                interface.get("primary_mac_address", {}).get("display", "")
                == self.mac_address
            ):
                netbox_target_interface = interface
                break

        ips = netbox_api.check_ip_by_interface(netbox_target_interface.get("id"))  # type: ignore
        if len(ips) == 0:
            logger.debug("No IPs assigned to this interface.")
            return
        if len(ips) > 2:
            logger.warning("Too many IPs assigned to this interface.")
            return
        # Reset Fields
        self.ip_address_v4 = None
        self.ip_address_v6 = None
        self.primary = False
        # Set fields
        machine_primary_ipv4 = netbox_machine.get("primary_ip4")
        machine_primary_ipv6 = netbox_machine.get("primary_ip6")
        for ip in ips:
            ip_obj = ipaddress.ip_network(ip.get("display"))  # type: ignore
            ip_id = ip.get("id", -1)
            if ip_obj.version == 4:
                self.ip_address_v4 = str(ip_obj)
            if ip_obj.version == 6:
                self.ip_address_v6 = str(ip_obj)
            if (
                machine_primary_ipv4 is not None
                and machine_primary_ipv4.get("id", 0) == ip_id
            ):
                self.primary = True
            if (
                machine_primary_ipv6 is not None
                and machine_primary_ipv6.get("id", 0) == ip_id
            ):
                self.primary = True
            self.save()
